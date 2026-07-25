"""Shared exception types for harness workflows."""


class HarnessError(Exception):
    """Base error for expected harness failures."""


class ConfigError(HarnessError):
    """Raised when configuration cannot be loaded or validated."""


class ShellPolicyError(HarnessError):
    """Raised when a shell command violates the command policy."""


class ModelError(HarnessError):
    """Raised when a model call fails."""


class SummaryValidationError(HarnessError):
    """Raised when model output fails summary validation."""
