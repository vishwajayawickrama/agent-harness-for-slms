from pathlib import Path

from typer.testing import CliRunner

from agent_harness_for_slms.cli import app

runner = CliRunner()


def test_version_prints_package_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_summarize_help_renders() -> None:
    result = runner.invoke(app, ["summarize", "--help"])

    assert result.exit_code == 0
    assert "Repository path to summarize" in result.output


def test_invalid_path_exits_non_zero() -> None:
    result = runner.invoke(app, ["summarize", "missing", "--dry-run"])

    assert result.exit_code != 0
    assert "Path does not exist" in result.output


def test_summarize_dry_run_succeeds_without_ollama(tmp_path: Path) -> None:
    result = runner.invoke(app, ["summarize", str(tmp_path), "--dry-run"])

    assert result.exit_code == 0
    assert "Planned shell commands" in result.output


def test_non_interactive_without_yes_fails(tmp_path: Path) -> None:
    result = runner.invoke(app, ["summarize", str(tmp_path)])

    assert result.exit_code != 0
    assert "requires --yes in non-interactive mode" in result.output
