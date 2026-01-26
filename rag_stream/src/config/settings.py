from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    RAG_BASE_URL: str
    RAG_API_KEY: str

    REQUEST_TIMEOUT: int = 300
    STREAM_TIMEOUT: int = 300

    SESSION_EXPIRE_HOURS: int = 1
    MAX_SESSIONS_PER_USER: int = 5

    DIFY_API_URL: str = "http://172.16.11.60/v1/chat-messages"
    DIFY_API_KEY: str = ""

    CHAT_IDS: Dict[str, str] = {}

    ACTIVE_ENV: str = "development"

    model_config = SettingsConfigDict(extra="ignore", case_sensitive=True)


DEFAULT_REQUEST_TIMEOUT = 300
DEFAULT_STREAM_TIMEOUT = 300
DEFAULT_SESSION_EXPIRE_HOURS = 1
DEFAULT_MAX_SESSIONS_PER_USER = 5
DEFAULT_DIFY_API_URL = "http://172.16.11.60/v1/chat-messages"


def _repo_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_yaml_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config file: {config_path}")

    raw = config_path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML structure in {config_path}")
    return data


def load_settings() -> Settings:
    base_dir = _repo_dir()
    yaml_path = base_dir / "config.yaml"
    cfg = _load_yaml_config(yaml_path)

    active_env = cfg.get("active_env")
    if not active_env or not isinstance(active_env, str):
        raise ValueError(f"Invalid active_env in {yaml_path}: {active_env!r}")

    environments = cfg.get("environments") or {}
    if not isinstance(environments, dict) or active_env not in environments:
        raise ValueError(f"Invalid active_env in {yaml_path}: {active_env!r}")

    env_file = base_dir / f".env.{active_env}"
    if not env_file.exists():
        raise FileNotFoundError(
            f"Missing env file for active_env={active_env!r}: {env_file}"
        )

    env_cfg = environments.get(active_env) or {}
    if not isinstance(env_cfg, dict):
        raise ValueError(f"Invalid environment config for {active_env!r} in {yaml_path}")

    return Settings(
        _env_file=str(env_file),
        ACTIVE_ENV=active_env,
        REQUEST_TIMEOUT=int(env_cfg.get("request_timeout", DEFAULT_REQUEST_TIMEOUT)),
        STREAM_TIMEOUT=int(env_cfg.get("stream_timeout", DEFAULT_STREAM_TIMEOUT)),
        SESSION_EXPIRE_HOURS=int(
            env_cfg.get("session_expire_hours", DEFAULT_SESSION_EXPIRE_HOURS)
        ),
        MAX_SESSIONS_PER_USER=int(
            env_cfg.get("max_sessions_per_user", DEFAULT_MAX_SESSIONS_PER_USER)
        ),
        DIFY_API_URL=str(env_cfg.get("dify_api_url", DEFAULT_DIFY_API_URL)),
        DIFY_API_KEY=str(env_cfg.get("dify_api_key", "")),
        CHAT_IDS=dict(env_cfg.get("chat_ids", {})),
    )


settings = load_settings()
