# Reference

This document captures early implementation decisions for the agent harness.

## First Iteration

The first iteration should be a CLI-based harness.

The goal is to test the core research question before building a complex user
interface or custom execution runtime:

Can structured prompting, workflow control, validation, and retries make a small
language model useful for narrow agentic tasks?

## Preferred Language

Python is the preferred language for the first version.

Python is practical for this project because it has strong support for:

- local model inference
- prompt orchestration
- tool execution
- file and repository inspection
- evaluation scripts
- test runners
- structured logging
- benchmark workflows

Recommended starting stack:

- CLI: Typer or Click
- Config: YAML or TOML
- Validation: Pydantic
- Testing: pytest
- Model runtime: Ollama first, then llama.cpp or transformers later
- Logs: JSONL files initially

## Project Shape

An early project structure could look like this:

```text
agent-harness-for-slms/
  harness/
    agents/
    tools/
    prompts/
    evaluators/
    runners/
  experiments/
  benchmarks/
  tests/
  README.md
  Reference.md
  pyproject.toml
```

## Bash Tool

The harness will need a shell execution tool. This is likely one of the most
important tools for early experiments, especially for workflows involving local
files, repositories, tests, and command-line programs.

For the early version, the harness should use a simple existing execution layer
instead of building a custom bash tool immediately.

The recommended first implementation is a small wrapper around Python's standard
library `subprocess` module.

This keeps the implementation explicit, dependency-light, and easy to replace
later.

Example shape:

```python
import subprocess
from dataclasses import dataclass


@dataclass
class CommandResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str


def run_command(command: str, cwd: str | None = None, timeout: int = 30) -> CommandResult:
    completed = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        text=True,
        capture_output=True,
        timeout=timeout,
    )

    return CommandResult(
        command=command,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
```

The model should not receive unrestricted shell access. It should interact with a
controlled tool interface.

Example tool interface:

```text
Tool: run_shell_command
Input:
{
  "command": "pytest",
  "cwd": ".",
  "timeout": 30
}
```

## Early Safety Constraints

The first shell tool should include basic safety and observability constraints:

- timeout every command
- limit stdout and stderr size
- use a fixed working directory
- log every command and result
- block obviously dangerous commands
- require the model to explain why it wants to run a command before execution

Examples of commands or patterns to block early:

- `rm -rf`
- `sudo`
- `chmod -R`
- `curl | sh`
- destructive filesystem operations outside the working directory

## Future Custom Bash Tool

After the harness becomes more stable, the shell execution layer can be replaced
with a custom bash tool.

A custom tool could support:

- persistent shell sessions
- command allow and deny lists
- stronger sandboxing
- filesystem permission controls
- structured command plans
- automatic output summarization
- approval gates
- replayable execution logs

## Recommended Direction

The first useful version should be:

```text
Python CLI harness
+ local model adapter
+ subprocess-based shell tool
+ strict logging
+ constrained workflow
+ validation and retry loop
```

This keeps the project focused on harness design while leaving room to build a
more sophisticated shell tool once the real requirements are clearer.
