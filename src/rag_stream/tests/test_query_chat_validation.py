from __future__ import annotations

import logging

from src.config.settings import Settings


def test_query_chat_config_should_warn_when_required_fields_missing(caplog):
    settings = Settings()
    settings.query_chat.enabled = True
    settings.query_chat.api_key = ""
    settings.query_chat.base_url = ""

    with caplog.at_level(logging.WARNING):
        settings.validate_query_chat_config()

    assert "QUERY_CHAT 配置不完整" in caplog.text
    assert "api_key, base_url" in caplog.text


def test_query_chat_config_should_mask_api_key_in_debug_log(caplog):
    settings = Settings()
    settings.query_chat.enabled = True
    settings.query_chat.api_key = "secret-key"
    settings.query_chat.base_url = "http://example.com/v1"
    settings.query_chat.model = "qwen"

    with caplog.at_level(logging.DEBUG):
        settings.validate_query_chat_config()

    assert "***" in caplog.text
    assert "secret-key" not in caplog.text
