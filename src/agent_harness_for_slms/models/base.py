"""Language model protocol and shared response types."""

from typing import Any, Protocol

from pydantic import BaseModel


class ModelResponse(BaseModel):
    text: str
    model: str
    provider: str
    raw: dict[str, Any] | None = None


class LanguageModel(Protocol):
    def generate(self, prompt: str) -> ModelResponse:
        """Generate text from a prompt."""
