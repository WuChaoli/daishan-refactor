from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.config.settings import QueryChatConfig
from src.utils.query_chat import QueryChat


def _build_fake_response(content: str):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


def _build_fake_client(response=None, error: Exception | None = None):
    def _create(**kwargs):
        if error is not None:
            raise error
        return response

    return SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=_create))
    )


def test_query_chat_should_log_invalid_config_when_build_client_failed():
    chat = QueryChat(QueryChatConfig(api_key="", base_url="", model=""))

    with patch("src.utils.query_chat.marker") as mocked_marker:
        with pytest.raises(ValueError, match="query_chat 配置不完整"):
            chat._build_client()

    mocked_marker.assert_any_call(
        "query_chat.config_invalid",
        {"base_url_set": False, "api_key_set": False, "model_set": False},
        level="ERROR",
    )


def test_query_chat_should_log_request_start_and_complete():
    source_query = "介绍一下浙江世倍尔新材料有限公司在园区的情况"
    target_query = "介绍一下在园区的情况"
    chat = QueryChat(
        QueryChatConfig(api_key="k", base_url="http://x", model="m", timeout=10)
    )
    fake_client = _build_fake_client(response=_build_fake_response(target_query))

    with patch("src.utils.query_chat.marker") as mocked_marker, patch.object(
        chat, "_get_client", return_value=fake_client
    ):
        result = chat.rewrite_query_remove_company(source_query)

    assert result == target_query
    mocked_marker.assert_any_call("query_chat.request_start", {"query_len": len(source_query)})
    mocked_marker.assert_any_call(
        "query_chat.request_complete",
        {"output_len": len(target_query), "normalized": True},
    )


def test_query_chat_should_log_empty_response_and_fallback():
    chat = QueryChat(
        QueryChatConfig(api_key="k", base_url="http://x", model="m", timeout=10)
    )
    fake_client = _build_fake_client(response=_build_fake_response("  "))
    source_query = "介绍一下浙江世倍尔新材料有限公司在园区的情况"

    with patch("src.utils.query_chat.marker") as mocked_marker, patch.object(
        chat, "_get_client", return_value=fake_client
    ):
        result = chat.rewrite_query_remove_company(source_query)

    assert result == source_query
    mocked_marker.assert_any_call("query_chat.empty_response", {}, level="WARNING")


def test_query_chat_should_log_request_failed_and_raise():
    chat = QueryChat(
        QueryChatConfig(api_key="k", base_url="http://x", model="m", timeout=10)
    )
    fake_client = _build_fake_client(error=RuntimeError("mock call failed"))

    with patch("src.utils.query_chat.marker") as mocked_marker, patch.object(
        chat, "_get_client", return_value=fake_client
    ):
        with pytest.raises(RuntimeError, match="mock call failed"):
            chat.rewrite_query_remove_company("浙江世倍尔新材料有限公司现在怎么样")

    mocked_marker.assert_any_call(
        "query_chat.request_failed",
        {"error": "mock call failed"},
        level="ERROR",
    )
