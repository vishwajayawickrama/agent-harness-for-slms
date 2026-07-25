"""Ollama HTTP model adapter."""

from typing import Any

import httpx

from agent_harness_for_slms.errors import ModelError
from agent_harness_for_slms.models.base import ModelResponse


class OllamaModel:
    def __init__(self, base_url: str, model: str, timeout: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def generate(self, prompt: str) -> ModelResponse:
        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=self.timeout,
            )
        except httpx.RequestError as exc:
            raise ModelError(
                f"Ollama is not reachable at {self.base_url}. "
                "Start Ollama or pass --ollama-url."
            ) from exc

        if response.status_code != 200:
            excerpt = response.text[:500]
            raise ModelError(
                f"Ollama returned HTTP {response.status_code}: {excerpt}"
            )

        raw: dict[str, Any] = response.json()
        text = raw.get("response")
        if not isinstance(text, str):
            raise ModelError("Ollama response did not include a text response.")

        return ModelResponse(
            text=text,
            model=self.model,
            provider="ollama",
            raw=raw,
        )
