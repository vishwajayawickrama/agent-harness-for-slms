"""Command-line interface for the harness."""

from importlib.metadata import version
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.json import JSON

from agent_harness_for_slms.config.settings import (
    SummaryCliOverrides,
    load_settings,
    merge_cli_overrides,
)
from agent_harness_for_slms.errors import HarnessError
from agent_harness_for_slms.runners.repo_summary import (
    DryRunResult,
    summarize_repository,
)

app = typer.Typer(
    help="A CLI agent harness for small language models.",
    no_args_is_help=True,
)
console = Console()


@app.callback(invoke_without_command=True)
def main(
    version_flag: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show the installed package version.",
            is_eager=True,
        ),
    ] = False,
) -> None:
    if version_flag:
        console.print(version("agent-harness-for-slms"))
        raise typer.Exit


@app.command()
def summarize(
    path: Annotated[
        Path,
        typer.Argument(help="Repository path to summarize."),
    ],
    model: Annotated[
        str | None,
        typer.Option("--model", help="Ollama model name."),
    ] = None,
    ollama_url: Annotated[
        str | None,
        typer.Option("--ollama-url", help="Ollama base URL."),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", help="Markdown report output path."),
    ] = None,
    log_path: Annotated[
        Path | None,
        typer.Option("--log-path", help="JSONL event log path."),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option("--config", help="TOML config file."),
    ] = None,
    timeout: Annotated[
        int | None,
        typer.Option("--timeout", help="Per-command shell timeout in seconds."),
    ] = None,
    max_output_chars: Annotated[
        int | None,
        typer.Option(
            "--max-output-chars",
            help="Maximum stdout/stderr characters retained per shell command.",
        ),
    ] = None,
    max_retries: Annotated[
        int | None,
        typer.Option(
            "--max-retries",
            help="Number of model retry attempts after validation failure.",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print the plan without executing it."),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option("--yes", help="Skip interactive command approval prompts."),
    ] = False,
) -> None:
    try:
        repo_path = path.expanduser().resolve()
        settings = load_settings(config, repo_path)
        settings = merge_cli_overrides(
            settings,
            SummaryCliOverrides(
                model=model,
                ollama_url=ollama_url,
                output=output,
                log_path=log_path,
                timeout=timeout,
                max_output_chars=max_output_chars,
                max_retries=max_retries,
            ),
        )
        result = summarize_repository(
            repo_path=repo_path,
            settings=settings,
            dry_run=dry_run,
            assume_yes=yes,
        )
    except HarnessError as exc:
        console.print(f"Error: {exc}", style="red")
        raise typer.Exit(1) from exc

    if isinstance(result, DryRunResult):
        console.print("Resolved settings:")
        console.print(JSON.from_data(result.settings.model_dump(mode="json")))
        console.print("Planned shell commands:")
        for command in result.command_plan:
            console.print(f"- {' '.join(command.command)}")
        return

    console.print(result.markdown)
    if result.output_path is not None:
        console.print(f"\nReport written to {result.output_path}")
    console.print(f"\nLog written to {result.log_path}")
