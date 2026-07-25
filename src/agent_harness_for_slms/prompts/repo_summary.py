"""Prompt construction for repository summaries."""

from typing import Any

REQUIRED_MARKDOWN_SECTIONS = """# Repository Summary

## Purpose

## Structure

## Important Files

## How To Work With This Repo

## Risks Or Unknowns

## Suggested Next Steps"""


def build_repo_summary_prompt(snapshot: Any) -> str:
    files = "\n".join(f"- {file}" for file in snapshot.files[:300])
    git_status = snapshot.git_status if snapshot.git_status is not None else "Unknown"
    return f"""You are summarizing a local software repository for an engineer.

Base your answer only on the repository context provided below. Do not invent
files, commands, dependencies, or behavior. Mention uncertainty explicitly when
the provided context is not enough.

Return concise Markdown using exactly these headings:

{REQUIRED_MARKDOWN_SECTIONS}

Repository root:
{snapshot.root}

Is Git repository:
{snapshot.is_git_repo}

Git status:
{git_status}

Files:
{files}

README excerpt:
{snapshot.readme_excerpt or "Not provided."}

pyproject.toml excerpt:
{snapshot.pyproject_excerpt or "Not provided."}

Reference.md excerpt:
{snapshot.reference_excerpt or "Not provided."}

Architecture excerpt:
{snapshot.architecture_excerpt or "Not provided."}
"""
