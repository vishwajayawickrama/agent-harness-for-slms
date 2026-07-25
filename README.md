# Agent Harness for Small Language Models

This project explores whether small language models can perform useful agentic
tasks when paired with a narrow, task-specific harness.

Large coding agents often rely on powerful general-purpose models. This project
takes the opposite approach: keep the model small, but make the surrounding
harness more structured. The harness should decompose tasks, manage context, call
tools, validate outputs, and retry with feedback.

## Core Question

Can a small language model produce reliable results on narrow tasks when the
harness carries more of the workflow burden?

## What Is a Harness?

An agent harness is the system around a model. It includes prompts, memory, tool
access, planning loops, validation, context selection, retries, and execution
controls.

In this project, the harness is expected to do more than simply pass user input
to a model. It should guide the model through a constrained workflow and verify
that each step is useful before moving forward.

## What Is a Small Language Model?

A small language model is a model that can run locally or cheaply, usually with
fewer parameters and weaker general reasoning than frontier models.

Small models may not perform well as general-purpose agents, but they may still
be useful when the task is narrow, the instructions are specific, and the harness
provides strong structure.

## Hypothesis

Small language models can become practically useful for agentic workflows when:

- the use case is narrow
- the model receives task-specific instructions
- the harness decomposes complex tasks into simpler steps
- tools are used for external work instead of relying only on model reasoning
- outputs are validated before they are accepted
- failures are fed back into the model for correction

## Initial Scope

The first version should target one constrained workflow instead of trying to
build a general-purpose agent.

Possible starting points:

- repository summarization
- simple code edits
- test generation
- shell command planning
- structured research over local files

The first implemented workflow is repository summarization through the CLI.

## Usage

Install dependencies:

```bash
uv sync
```

Install Ollama and pull the default small coding model:

```bash
ollama pull qwen2.5-coder:1.5b
```

Preview the planned read-only shell commands:

```bash
uv run agent-harness-for-slms summarize . --dry-run
```

Generate a repository summary with local Ollama:

```bash
uv run agent-harness-for-slms summarize . --yes
```

Write the summary to a file:

```bash
uv run agent-harness-for-slms summarize . --yes --output reports/summary.md
```

The command writes structured JSONL run logs to `.harness/logs/` by default.

## Project Structure

The Python package is organized around small harness responsibilities:

- `agents`: task-specific control loops
- `models`: language model runtime adapters
- `tools`: controlled tool interfaces
- `prompts`: prompt templates and assembly
- `runners`: CLI-executed workflows
- `validation`: output checks and retry decisions
- `evaluators`: experiment scoring helpers
- `logging`: structured logs and replay support
- `config`: configuration loading and validation

See [docs/architecture.md](docs/architecture.md) for the current architecture
notes.

See [docs/v1-repo-summarizer.md](docs/v1-repo-summarizer.md) for the V1
repository summarizer behavior.

## Goal

The goal is to test whether a focused harness can extract more reliable behavior
from small language models without depending on expensive frontier models.

This project should eventually compare small models across the same task and
measure whether harness design improves their success rate.

## Next Steps

- Pick the first narrow workflow to support
- Choose one or two small models to test
- Define success metrics for the workflow
- Design the first harness loop
- Add validation and retry behavior
- Record results across models and harness versions
