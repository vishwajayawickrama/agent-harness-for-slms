"""Configuration models and loading helpers."""

import tomllib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, ValidationError

from agent_harness_for_slms.errors import ConfigError


class ModelSettings(BaseModel):
    model_config = ConfigDict(validate_default=True)

    provider: Literal["ollama"] = "ollama"
    name: str = Field(default="qwen2.5-coder:1.5b", min_length=1)
    base_url: HttpUrl = "http://localhost:11434"


class ShellSettings(BaseModel):
    timeout: int = Field(default=30, ge=1, le=300)
    max_output_chars: int = Field(default=12000, ge=1000, le=200000)
    require_approval: bool = True


class SummarySettings(BaseModel):
    max_retries: int = Field(default=1, ge=0, le=5)
    output: Path | None = None
    log_path: Path | None = None


class HarnessSettings(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    model: ModelSettings = Field(default_factory=ModelSettings)
    shell: ShellSettings = Field(default_factory=ShellSettings)
    summary: SummarySettings = Field(default_factory=SummarySettings)


class SummaryCliOverrides(BaseModel):
    model: str | None = None
    ollama_url: str | None = None
    output: Path | None = None
    log_path: Path | None = None
    timeout: int | None = None
    max_output_chars: int | None = None
    max_retries: int | None = None


def load_settings(config_path: Path | None, repo_path: Path) -> HarnessSettings:
    selected_path = config_path
    if selected_path is None:
        default_path = repo_path / ".harness" / "config.toml"
        selected_path = default_path if default_path.exists() else None

    if selected_path is None:
        return HarnessSettings()

    if not selected_path.exists():
        raise ConfigError(f"Config file does not exist: {selected_path}")

    try:
        with selected_path.open("rb") as config_file:
            raw_settings = tomllib.load(config_file)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Config file is not valid TOML: {selected_path}") from exc
    except OSError as exc:
        raise ConfigError(f"Could not read config file: {selected_path}") from exc

    try:
        return HarnessSettings.model_validate(raw_settings)
    except ValidationError as exc:
        raise ConfigError(str(exc)) from exc


def merge_cli_overrides(
    settings: HarnessSettings,
    overrides: SummaryCliOverrides,
) -> HarnessSettings:
    data = settings.model_dump()

    if overrides.model is not None:
        data["model"]["name"] = overrides.model
    if overrides.ollama_url is not None:
        data["model"]["base_url"] = overrides.ollama_url
    if overrides.output is not None:
        data["summary"]["output"] = overrides.output
    if overrides.log_path is not None:
        data["summary"]["log_path"] = overrides.log_path
    if overrides.timeout is not None:
        data["shell"]["timeout"] = overrides.timeout
    if overrides.max_output_chars is not None:
        data["shell"]["max_output_chars"] = overrides.max_output_chars
    if overrides.max_retries is not None:
        data["summary"]["max_retries"] = overrides.max_retries

    try:
        return HarnessSettings.model_validate(data)
    except ValidationError as exc:
        raise ConfigError(str(exc)) from exc
