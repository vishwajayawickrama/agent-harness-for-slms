from pathlib import Path

import pytest

from agent_harness_for_slms.config.settings import (
    HarnessSettings,
    SummaryCliOverrides,
    load_settings,
    merge_cli_overrides,
)
from agent_harness_for_slms.errors import ConfigError


def test_defaults_load_without_config(tmp_path: Path) -> None:
    settings = load_settings(None, tmp_path)

    assert settings.model.name == "qwen2.5-coder:1.5b"
    assert str(settings.model.base_url) == "http://localhost:11434/"


def test_default_config_is_discovered(tmp_path: Path) -> None:
    config_path = tmp_path / ".harness" / "config.toml"
    config_path.parent.mkdir()
    config_path.write_text('[model]\nname = "llama3.2:3b"\n', encoding="utf-8")

    settings = load_settings(None, tmp_path)

    assert settings.model.name == "llama3.2:3b"


def test_explicit_config_overrides_default_path(tmp_path: Path) -> None:
    default_path = tmp_path / ".harness" / "config.toml"
    default_path.parent.mkdir()
    default_path.write_text('[model]\nname = "default"\n', encoding="utf-8")
    explicit_path = tmp_path / "harness.toml"
    explicit_path.write_text('[model]\nname = "explicit"\n', encoding="utf-8")

    settings = load_settings(explicit_path, tmp_path)

    assert settings.model.name == "explicit"


def test_cli_overrides_win_over_toml() -> None:
    settings = HarnessSettings()
    merged = merge_cli_overrides(
        settings,
        SummaryCliOverrides(model="override", timeout=10),
    )

    assert merged.model.name == "override"
    assert merged.shell.timeout == 10


def test_invalid_provider_fails(tmp_path: Path) -> None:
    config_path = tmp_path / "harness.toml"
    config_path.write_text('[model]\nprovider = "other"\n', encoding="utf-8")

    with pytest.raises(ConfigError):
        load_settings(config_path, tmp_path)


def test_invalid_timeout_fails() -> None:
    with pytest.raises(ConfigError):
        merge_cli_overrides(HarnessSettings(), SummaryCliOverrides(timeout=0))
