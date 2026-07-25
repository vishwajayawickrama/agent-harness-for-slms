# V1 Repository Summarizer

The first harness workflow summarizes a local repository with a controlled
shell tool and a local Ollama model.

## Command

```bash
agent-harness-for-slms summarize PATH [OPTIONS]
```

Common usage:

```bash
uv run agent-harness-for-slms summarize . --dry-run
uv run agent-harness-for-slms summarize . --yes
uv run agent-harness-for-slms summarize . --yes --output reports/summary.md
```

## Model Runtime

V1 supports Ollama over HTTP.

Default model:

```text
qwen2.5-coder:1.5b
```

Default endpoint:

```text
http://localhost:11434
```

Setup:

```bash
ollama pull qwen2.5-coder:1.5b
```

## Configuration

The command accepts CLI flags and TOML configuration. CLI flags override TOML.

Default config lookup:

```text
.harness/config.toml
```

Example:

```toml
[model]
provider = "ollama"
name = "qwen2.5-coder:1.5b"
base_url = "http://localhost:11434"

[shell]
timeout = 30
max_output_chars = 12000
require_approval = true

[summary]
max_retries = 1
output = "reports/summary.md"
log_path = ".harness/logs/repo-summary.jsonl"
```

## Shell Safety

V1 uses `subprocess.run` with `shell=False`. The model never receives raw
unrestricted shell access.

Allowed command families:

```text
pwd
git status --short
git ls-files
find
ls
```

Blocked command patterns:

```text
rm
sudo
chmod
chown
mkfs
dd
curl
wget
ssh
scp
rsync
```

By default, the command asks for approval before executing shell commands. Use
`--yes` for non-interactive runs and automation. Use `--dry-run` to print the
resolved settings and command plan without shell execution or model calls.

## Output

The model must return Markdown with these sections:

```markdown
# Repository Summary

## Purpose

## Structure

## Important Files

## How To Work With This Repo

## Risks Or Unknowns

## Suggested Next Steps
```

The harness validates the required headings, minimum length, and obvious
placeholder text. Failed summaries are retried according to `max_retries`.

## Logging

Non-dry-run executions write JSONL events.

Default path:

```text
.harness/logs/<YYYYMMDD-HHMMSS>-repo-summary.jsonl
```

Important event types:

```text
run_started
settings_resolved
command_plan_created
command_started
command_finished
snapshot_created
model_call_started
model_call_finished
validation_finished
retry_started
report_written
run_finished
run_failed
```

## Known Limitations

- Only Ollama is supported as a real model provider.
- The workflow only summarizes repositories; it does not edit files.
- The shell policy is intentionally conservative.
- Summary quality depends on the local model and the available repository
  context.
