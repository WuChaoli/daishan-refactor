from __future__ import annotations

from pathlib import Path

from src.config.settings import Settings


def test_query_chat_config_should_load_from_yaml(tmp_path: Path):
    yaml_path = tmp_path / "config.yaml"
    yaml_path.write_text(
        """
query_chat:
  enabled: true
  api_key: "yaml-key"
  base_url: "http://yaml.example.com/v1"
  model: "yaml-model"
  timeout: 15
  temperature: 0.2
""".strip(),
        encoding="utf-8",
    )

    settings = Settings.load_from_yaml(yaml_path)

    assert settings.query_chat.enabled is True
    assert settings.query_chat.api_key == "yaml-key"
    assert settings.query_chat.base_url == "http://yaml.example.com/v1"
    assert settings.query_chat.model == "yaml-model"
    assert settings.query_chat.timeout == 15
    assert settings.query_chat.temperature == 0.2


def test_query_chat_config_should_support_env_override(tmp_path: Path, monkeypatch):
    yaml_path = tmp_path / "config.yaml"
    yaml_path.write_text(
        """
query_chat:
  enabled: true
  api_key: "yaml-key"
  base_url: "http://yaml.example.com/v1"
  model: "yaml-model"
  timeout: 15
  temperature: 0.2
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv("QUERY_CHAT_API_KEY", "env-key")
    monkeypatch.setenv("QUERY_CHAT_BASE_URL", "http://env.example.com/v1")
    monkeypatch.setenv("QUERY_CHAT_MODEL", "env-model")
    monkeypatch.setenv("QUERY_CHAT_ENABLED", "false")
    monkeypatch.setenv("QUERY_CHAT_TIMEOUT", "9")
    monkeypatch.setenv("QUERY_CHAT_TEMPERATURE", "0.0")

    settings = Settings.load_from_yaml_with_env_override(yaml_path)

    assert settings.query_chat.enabled is False
    assert settings.query_chat.api_key == "env-key"
    assert settings.query_chat.base_url == "http://env.example.com/v1"
    assert settings.query_chat.model == "env-model"
    assert settings.query_chat.timeout == 9
    assert settings.query_chat.temperature == 0.0
