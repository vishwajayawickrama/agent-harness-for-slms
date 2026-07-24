# Architecture

The harness is organized around narrow, testable responsibilities. The first
implementation should keep these boundaries small and explicit.

## Package Areas

- `agents`: task-specific control loops that decide the next harness action
- `config`: project configuration loading and validation
- `evaluators`: scoring and comparison helpers for experiments
- `logging`: structured event logs and replay support
- `models`: adapters for local and remote language model runtimes
- `prompts`: prompt templates and prompt assembly utilities
- `runners`: executable workflows exposed through the CLI
- `tools`: controlled tool interfaces, including shell execution
- `validation`: output checks and retry decisions

## Top-Level Workspaces

- `benchmarks`: reusable inputs and expected outcomes for harness evaluation
- `experiments`: one-off runs, notes, and comparison artifacts
- `tests`: automated tests grouped to match the package areas

## Design Notes

The early harness should prefer simple interfaces over framework-heavy
abstractions. Each package area should start with explicit data structures and
small functions, then evolve only when repeated behavior makes the abstraction
useful.
