"""Repository summarization runner."""

import sys
from datetime import datetime
from pathlib import Path
from typing import TextIO

from pydantic import BaseModel

from agent_harness_for_slms.config.settings import HarnessSettings
from agent_harness_for_slms.errors import HarnessError, SummaryValidationError
from agent_harness_for_slms.logging.jsonl import JsonlEventLogger
from agent_harness_for_slms.models.base import LanguageModel
from agent_harness_for_slms.models.ollama import OllamaModel
from agent_harness_for_slms.prompts.repo_summary import build_repo_summary_prompt
from agent_harness_for_slms.tools.shell import CommandResult, ShellCommand, ShellTool
from agent_harness_for_slms.validation.repo_summary import validate_repo_summary


class RepositorySnapshot(BaseModel):
    root: Path
    is_git_repo: bool
    git_status: str | None
    files: list[str]
    readme_excerpt: str | None
    pyproject_excerpt: str | None
    reference_excerpt: str | None = None
    architecture_excerpt: str | None = None


class SummaryResult(BaseModel):
    markdown: str
    output_path: Path | None
    log_path: Path
    attempts: int


class DryRunResult(BaseModel):
    repo_path: Path
    settings: HarnessSettings
    command_plan: list[ShellCommand]


def default_log_path(repo_path: Path) -> Path:
    timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    return repo_path / ".harness" / "logs" / f"{timestamp}-repo-summary.jsonl"


def build_command_plan(repo_path: Path) -> list[ShellCommand]:
    return [
        ShellCommand(command=["pwd"], purpose="Confirm repository root.", cwd=repo_path),
        ShellCommand(
            command=["git", "status", "--short"],
            purpose="Check whether the repository has uncommitted changes.",
            cwd=repo_path,
        ),
        ShellCommand(
            command=["git", "ls-files"],
            purpose="List Git-tracked files for repository structure.",
            cwd=repo_path,
        ),
    ]


def summarize_repository(
    repo_path: Path,
    settings: HarnessSettings,
    dry_run: bool = False,
    assume_yes: bool = False,
    model: LanguageModel | None = None,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
) -> SummaryResult | DryRunResult:
    repo_root = repo_path.expanduser().resolve()
    if not repo_root.exists():
        raise HarnessError(f"Path does not exist: {repo_root}")
    if not repo_root.is_dir():
        raise HarnessError(f"Path is not a directory: {repo_root}")

    settings = _with_default_log_path(settings, repo_root)
    command_plan = build_command_plan(repo_root)

    if dry_run:
        return DryRunResult(
            repo_path=repo_root,
            settings=settings,
            command_plan=command_plan,
        )

    input_stream = stdin or sys.stdin
    output_stream = stdout or sys.stdout
    if settings.shell.require_approval and not assume_yes:
        if not input_stream.isatty():
            raise HarnessError("Shell command approval requires --yes in non-interactive mode.")
        _prompt_for_approval(command_plan, input_stream, output_stream)

    logger = JsonlEventLogger(settings.summary.log_path or default_log_path(repo_root))
    logger.write("run_started", {"repo_path": str(repo_root)})
    logger.write("settings_resolved", settings.model_dump(mode="json"))
    logger.write(
        "command_plan_created",
        {"commands": [command.model_dump(mode="json") for command in command_plan]},
    )

    try:
        shell = ShellTool(
            timeout=settings.shell.timeout,
            max_output_chars=settings.shell.max_output_chars,
        )
        results = _execute_command_plan(shell, command_plan, logger)
        snapshot = _create_snapshot(repo_root, results)
        logger.write("snapshot_created", snapshot.model_dump(mode="json"))

        prompt = build_repo_summary_prompt(snapshot)
        active_model = model or OllamaModel(
            base_url=str(settings.model.base_url),
            model=settings.model.name,
        )
        markdown, attempts = _generate_valid_summary(
            active_model,
            prompt,
            settings.summary.max_retries,
            logger,
        )

        output_path = settings.summary.output
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown, encoding="utf-8")
            logger.write("report_written", {"output_path": str(output_path)})

        logger.write("run_finished", {"attempts": attempts})
        return SummaryResult(
            markdown=markdown,
            output_path=output_path,
            log_path=logger.path,
            attempts=attempts,
        )
    except Exception as exc:
        logger.write("run_failed", {"error": str(exc)})
        raise


def _with_default_log_path(
    settings: HarnessSettings,
    repo_root: Path,
) -> HarnessSettings:
    if settings.summary.log_path is not None:
        return settings
    data = settings.model_dump()
    data["summary"]["log_path"] = default_log_path(repo_root)
    return HarnessSettings.model_validate(data)


def _execute_command_plan(
    shell: ShellTool,
    command_plan: list[ShellCommand],
    logger: JsonlEventLogger,
) -> list[CommandResult]:
    results: list[CommandResult] = []
    for command in command_plan:
        logger.write("command_started", command.model_dump(mode="json"))
        result = shell.run(command)
        logger.write("command_finished", result.model_dump(mode="json"))
        results.append(result)
    if _git_ls_files_failed(results):
        fallback = ShellCommand(
            command=["find", ".", "-maxdepth", "4", "-type", "f"],
            purpose="List files for non-Git repository structure.",
            cwd=command_plan[0].cwd,
        )
        logger.write("command_started", fallback.model_dump(mode="json"))
        result = shell.run(fallback)
        logger.write("command_finished", result.model_dump(mode="json"))
        results.append(result)
    return results


def _git_ls_files_failed(results: list[CommandResult]) -> bool:
    for result in results:
        if result.command == ["git", "ls-files"]:
            return result.exit_code != 0
    return True


def _create_snapshot(repo_root: Path, results: list[CommandResult]) -> RepositorySnapshot:
    git_status = None
    files: list[str] = []
    is_git_repo = False

    for result in results:
        if result.command == ["git", "status", "--short"] and result.exit_code == 0:
            git_status = result.stdout
            is_git_repo = True
        if result.command == ["git", "ls-files"] and result.exit_code == 0:
            files = [line for line in result.stdout.splitlines() if line.strip()]
        if result.command[:1] == ["find"] and result.exit_code == 0 and not files:
            files = [
                line.removeprefix("./")
                for line in result.stdout.splitlines()
                if line.strip()
            ]

    return RepositorySnapshot(
        root=repo_root,
        is_git_repo=is_git_repo,
        git_status=git_status,
        files=files[:500],
        readme_excerpt=_read_excerpt(repo_root / "README.md"),
        pyproject_excerpt=_read_excerpt(repo_root / "pyproject.toml"),
        reference_excerpt=_read_excerpt(repo_root / "Reference.md"),
        architecture_excerpt=_read_excerpt(repo_root / "docs" / "architecture.md"),
    )


def _read_excerpt(path: Path, max_chars: int = 6000) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:max_chars]
    except OSError:
        return None


def _generate_valid_summary(
    model: LanguageModel,
    prompt: str,
    max_retries: int,
    logger: JsonlEventLogger,
) -> tuple[str, int]:
    current_prompt = prompt
    for attempt in range(1, max_retries + 2):
        logger.write("model_call_started", {"attempt": attempt})
        response = model.generate(current_prompt)
        logger.write(
            "model_call_finished",
            {"attempt": attempt, "model": response.model, "provider": response.provider},
        )
        validation = validate_repo_summary(response.text)
        logger.write(
            "validation_finished",
            {"attempt": attempt, "valid": validation.valid, "errors": validation.errors},
        )
        if validation.valid:
            return response.text, attempt
        if attempt <= max_retries:
            logger.write("retry_started", {"attempt": attempt + 1})
            current_prompt = (
                prompt
                + "\n\nThe previous response failed validation:\n"
                + "\n".join(f"- {error}" for error in validation.errors)
                + "\nReturn a corrected Markdown report with all required headings."
            )

    raise SummaryValidationError(
        "Summary validation failed after "
        f"{max_retries + 1} attempt(s): {', '.join(validation.errors)}"
    )


def _prompt_for_approval(
    command_plan: list[ShellCommand],
    stdin: TextIO,
    stdout: TextIO,
) -> None:
    stdout.write("Planned shell commands:\n")
    stdout.writelines(
        f"- {' '.join(command.command)}: {command.purpose}\n"
        for command in command_plan
    )
    stdout.write("Run these commands? [y/N] ")
    stdout.flush()
    answer = stdin.readline().strip().lower()
    if answer not in {"y", "yes"}:
        raise HarnessError("Shell command execution was not approved.")
