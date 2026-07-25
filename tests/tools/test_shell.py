from pathlib import Path

import pytest

from agent_harness_for_slms.errors import ShellPolicyError
from agent_harness_for_slms.tools.shell import ShellCommand, ShellTool


def test_allowed_command_succeeds(tmp_path: Path) -> None:
    result = ShellTool().run(
        ShellCommand(command=["pwd"], purpose="test", cwd=tmp_path)
    )

    assert result.exit_code == 0
    assert str(tmp_path) in result.stdout


def test_stdout_and_stderr_are_captured(tmp_path: Path) -> None:
    result = ShellTool().run(
        ShellCommand(command=["ls", "missing"], purpose="test", cwd=tmp_path)
    )

    assert result.exit_code != 0
    assert result.stderr


def test_output_truncation_works(tmp_path: Path) -> None:
    for index in range(5):
        (tmp_path / f"file-{index}.txt").write_text("x", encoding="utf-8")

    result = ShellTool(max_output_chars=10).run(
        ShellCommand(command=["ls"], purpose="test", cwd=tmp_path)
    )

    assert "[truncated]" in result.stdout


def test_denied_command_raises_policy_error(tmp_path: Path) -> None:
    with pytest.raises(ShellPolicyError):
        ShellTool().run(ShellCommand(command=["rm", "-rf", "."], purpose="bad", cwd=tmp_path))


def test_command_uses_repository_cwd(tmp_path: Path) -> None:
    result = ShellTool().run(
        ShellCommand(command=["pwd"], purpose="test", cwd=tmp_path)
    )

    assert result.cwd == tmp_path


def test_timeout_returns_structured_result(tmp_path: Path) -> None:
    result = ShellTool(timeout=1).run(
        ShellCommand(
            command=["find", ".", "-exec", "sleep", "2", ";"],
            purpose="timeout",
            cwd=tmp_path,
        )
    )

    assert result.timed_out is True
    assert result.exit_code == 124
