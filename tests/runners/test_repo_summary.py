from pathlib import Path

from agent_harness_for_slms.config.settings import HarnessSettings
from agent_harness_for_slms.models.base import ModelResponse
from agent_harness_for_slms.runners.repo_summary import (
    DryRunResult,
    summarize_repository,
)
from tests.validation.test_repo_summary import VALID_MARKDOWN


class FakeModel:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls = 0

    def generate(self, prompt: str) -> ModelResponse:
        self.calls += 1
        return ModelResponse(
            text=self.responses.pop(0),
            model="fake",
            provider="fake",
            raw=None,
        )


def test_dry_run_returns_command_plan_without_model_call(tmp_path: Path) -> None:
    model = FakeModel([VALID_MARKDOWN])

    result = summarize_repository(tmp_path, HarnessSettings(), dry_run=True, model=model)

    assert isinstance(result, DryRunResult)
    assert model.calls == 0


def test_successful_run_returns_markdown(tmp_path: Path) -> None:
    result = summarize_repository(
        tmp_path,
        HarnessSettings(),
        assume_yes=True,
        model=FakeModel([VALID_MARKDOWN]),
    )

    assert result.markdown == VALID_MARKDOWN
    assert result.attempts == 1


def test_validation_retry_calls_model_again(tmp_path: Path) -> None:
    model = FakeModel(["bad", VALID_MARKDOWN])
    settings = HarnessSettings()
    settings.summary.max_retries = 1

    result = summarize_repository(tmp_path, settings, assume_yes=True, model=model)

    assert result.attempts == 2
    assert model.calls == 2


def test_output_file_is_written_when_configured(tmp_path: Path) -> None:
    settings = HarnessSettings()
    settings.summary.output = tmp_path / "summary.md"

    summarize_repository(
        tmp_path,
        settings,
        assume_yes=True,
        model=FakeModel([VALID_MARKDOWN]),
    )

    assert settings.summary.output.read_text(encoding="utf-8") == VALID_MARKDOWN


def test_log_file_records_lifecycle_events(tmp_path: Path) -> None:
    settings = HarnessSettings()
    settings.summary.log_path = tmp_path / "events.jsonl"

    summarize_repository(
        tmp_path,
        settings,
        assume_yes=True,
        model=FakeModel([VALID_MARKDOWN]),
    )

    logs = settings.summary.log_path.read_text(encoding="utf-8")
    assert "run_started" in logs
    assert "run_finished" in logs
