from agent_harness_for_slms.validation.repo_summary import validate_repo_summary

VALID_MARKDOWN = """# Repository Summary

## Purpose

This repository contains a small Python command-line harness for summarizing
repositories with a local model. It uses structured modules and explicit
validation to keep the first workflow narrow and observable.

## Structure

The source package contains areas for CLI, configuration, model adapters, shell
tools, prompt building, validation, runners, and structured logging.

## Important Files

README.md explains the project. pyproject.toml defines packaging and
dependencies. The src package holds the implementation.

## How To Work With This Repo

Install dependencies with uv, run tests with pytest, and invoke the CLI through
the package script.

## Risks Or Unknowns

The real model quality depends on the local Ollama model and available context.

## Suggested Next Steps

Add more workflows, broaden evaluation fixtures, and compare small model results.
"""


def test_valid_markdown_passes() -> None:
    assert validate_repo_summary(VALID_MARKDOWN).valid is True


def test_missing_heading_fails() -> None:
    result = validate_repo_summary(VALID_MARKDOWN.replace("## Purpose", "## Goal"))

    assert result.valid is False
    assert "missing heading ## Purpose" in result.errors


def test_empty_output_fails() -> None:
    assert validate_repo_summary("").valid is False


def test_too_short_output_fails() -> None:
    result = validate_repo_summary("# Repository Summary")

    assert result.valid is False
    assert "summary is shorter than 300 characters" in result.errors


def test_placeholder_text_fails() -> None:
    result = validate_repo_summary(VALID_MARKDOWN + "\nTODO")

    assert result.valid is False
