"""Controlled subprocess-backed shell tool."""

import subprocess
import time
from pathlib import Path

from pydantic import BaseModel, Field

from agent_harness_for_slms.errors import ShellPolicyError

BLOCKED_PATTERNS = {
    "rm",
    "sudo",
    "chmod",
    "chown",
    "mkfs",
    "dd",
    "curl",
    "wget",
    "ssh",
    "scp",
    "rsync",
}

ALLOWED_EXECUTABLES = {"pwd", "git", "find", "ls"}
ALLOWED_GIT_COMMANDS = {("status", "--short"), ("ls-files",)}


class ShellCommand(BaseModel):
    command: list[str] = Field(min_length=1)
    purpose: str = Field(min_length=1)
    cwd: Path


class CommandResult(BaseModel):
    command: list[str]
    purpose: str
    cwd: Path
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool
    duration_ms: int


class ShellTool:
    def __init__(self, timeout: int = 30, max_output_chars: int = 12000) -> None:
        self.timeout = timeout
        self.max_output_chars = max_output_chars

    def run(self, command: ShellCommand) -> CommandResult:
        self._validate_policy(command.command)
        start = time.monotonic()
        try:
            completed = subprocess.run(
                command.command,
                cwd=command.cwd,
                shell=False,
                text=True,
                capture_output=True,
                timeout=self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            return CommandResult(
                command=command.command,
                purpose=command.purpose,
                cwd=command.cwd,
                exit_code=124,
                stdout=self._truncate(exc.stdout or ""),
                stderr=self._truncate(exc.stderr or f"Command timed out after {self.timeout}s"),
                timed_out=True,
                duration_ms=duration_ms,
            )

        duration_ms = int((time.monotonic() - start) * 1000)
        return CommandResult(
            command=command.command,
            purpose=command.purpose,
            cwd=command.cwd,
            exit_code=completed.returncode,
            stdout=self._truncate(completed.stdout),
            stderr=self._truncate(completed.stderr),
            timed_out=False,
            duration_ms=duration_ms,
        )

    def _truncate(self, value: str) -> str:
        if len(value) <= self.max_output_chars:
            return value
        return value[: self.max_output_chars] + "\n[truncated]"

    def _validate_policy(self, command: list[str]) -> None:
        executable = Path(command[0]).name
        lowered_parts = {part.lower() for part in command}
        blocked = BLOCKED_PATTERNS.intersection(lowered_parts)
        if blocked:
            raise ShellPolicyError(f"Command denied by shell policy: {min(blocked)}")
        if executable not in ALLOWED_EXECUTABLES:
            raise ShellPolicyError(f"Command denied by shell policy: {executable}")
        if executable == "git":
            git_args = tuple(command[1:])
            if git_args not in ALLOWED_GIT_COMMANDS:
                raise ShellPolicyError(
                    f"Command denied by shell policy: git {' '.join(git_args)}"
                )
