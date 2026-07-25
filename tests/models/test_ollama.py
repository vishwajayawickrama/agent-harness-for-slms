import httpx
import pytest

from agent_harness_for_slms.errors import ModelError
from agent_harness_for_slms.models.ollama import OllamaModel


def test_successful_response_parses_response(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(*args: object, **kwargs: object) -> httpx.Response:
        return httpx.Response(200, json={"response": "summary"})

    monkeypatch.setattr(httpx, "post", fake_post)

    response = OllamaModel("http://localhost:11434", "model").generate("prompt")

    assert response.text == "summary"
    assert response.provider == "ollama"


def test_connection_failure_becomes_model_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(*args: object, **kwargs: object) -> httpx.Response:
        raise httpx.ConnectError("nope")

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(ModelError):
        OllamaModel("http://localhost:11434", "model").generate("prompt")


def test_non_200_response_becomes_model_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(*args: object, **kwargs: object) -> httpx.Response:
        return httpx.Response(500, text="bad")

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(ModelError):
        OllamaModel("http://localhost:11434", "model").generate("prompt")


def test_missing_response_becomes_model_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(*args: object, **kwargs: object) -> httpx.Response:
        return httpx.Response(200, json={"done": True})

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(ModelError):
        OllamaModel("http://localhost:11434", "model").generate("prompt")
