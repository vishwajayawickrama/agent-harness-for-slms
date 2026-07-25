from pathlib import Path

from agent_harness_for_slms.prompts.repo_summary import build_repo_summary_prompt
from agent_harness_for_slms.runners.repo_summary import RepositorySnapshot


def test_prompt_contains_repo_file_list() -> None:
    prompt = build_repo_summary_prompt(
        RepositorySnapshot(
            root=Path("."),
            is_git_repo=True,
            git_status="",
            files=["README.md", "pyproject.toml"],
            readme_excerpt="Readme",
            pyproject_excerpt="Project",
        )
    )

    assert "README.md" in prompt
    assert "pyproject.toml" in prompt


def test_prompt_contains_required_output_headings() -> None:
    prompt = build_repo_summary_prompt(
        RepositorySnapshot(
            root=Path("."),
            is_git_repo=True,
            git_status="",
            files=[],
            readme_excerpt=None,
            pyproject_excerpt=None,
        )
    )

    assert "# Repository Summary" in prompt
    assert "## Suggested Next Steps" in prompt


def test_prompt_instructs_model_not_to_invent_files() -> None:
    prompt = build_repo_summary_prompt(
        RepositorySnapshot(
            root=Path("."),
            is_git_repo=True,
            git_status="",
            files=[],
            readme_excerpt=None,
            pyproject_excerpt=None,
        )
    )

    assert "Do not invent" in prompt
