"""Validation for repository summary Markdown."""

from pydantic import BaseModel

REQUIRED_HEADINGS = [
    "# Repository Summary",
    "## Purpose",
    "## Structure",
    "## Important Files",
    "## How To Work With This Repo",
    "## Risks Or Unknowns",
    "## Suggested Next Steps",
]

PLACEHOLDER_PATTERNS = [
    "TODO",
    "lorem ipsum",
    "I cannot",
    "as an AI language model",
]


class ValidationResult(BaseModel):
    valid: bool
    errors: list[str]


def validate_repo_summary(markdown: str) -> ValidationResult:
    errors: list[str] = []
    stripped = markdown.strip()
    if not stripped:
        errors.append("summary is empty")
    if len(stripped) < 300:
        errors.append("summary is shorter than 300 characters")

    for heading in REQUIRED_HEADINGS:
        if heading not in markdown:
            errors.append(f"missing heading {heading}")

    lower_markdown = markdown.lower()
    for pattern in PLACEHOLDER_PATTERNS:
        if pattern.lower() in lower_markdown:
            errors.append(f"contains placeholder text {pattern}")

    return ValidationResult(valid=not errors, errors=errors)
