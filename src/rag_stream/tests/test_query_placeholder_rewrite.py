from __future__ import annotations

import sys
import types
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

if "DaiShanSQL" not in sys.modules:
    daishan_sql_stub = types.ModuleType("DaiShanSQL")

    class _StubSqlFixed:
        @staticmethod
        def sql_ChemicalCompanyInfo():
            return ""

        @staticmethod
        def sql_SecuritySituation():
            return ""

    class _StubServer:
        def __init__(self):
            self.sqlFixed = _StubSqlFixed()

        @staticmethod
        def get_sql_result(*args, **kwargs):
            return ""

        @staticmethod
        def judgeQuery(*args, **kwargs):
            return []

    daishan_sql_stub.Server = _StubServer
    sys.modules["DaiShanSQL"] = daishan_sql_stub

from rag_stream.config.settings import QueryChatConfig
from rag_stream.services.chat_general_service import _build_query_variants
from rag_stream.services.fixed_question_flow_service import replace_daishan_zone_alias
from rag_stream.utils.query_chat import QueryChat


class _CaptureCreate:
    def __init__(self, content: str):
        self.content = content
        self.kwargs = None

    def __call__(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))]
        )


def test_replace_daishan_zone_alias_should_normalize_all_supported_aliases():
    source_query = "岱山经开区、岱山经济开发区和岱山化工园区的情况"

    rewritten = replace_daishan_zone_alias(source_query)

    assert rewritten == "园区、园区和园区的情况"


@pytest.mark.asyncio
async def test_build_query_variants_should_generate_q1_from_normalized_q2():
    source_query = "张三在岱山经济开发区的浙江某某有限公司有什么注册安全工程师证书"

    with patch(
        "rag_stream.services.chat_general_service.replace_economic_zone",
        new=AsyncMock(return_value="某人在园区的某公司有什么某证书"),
    ) as mocked_replace_economic_zone:
        q1, q2 = await _build_query_variants(source_query)

    assert q2 == "张三在园区的浙江某某有限公司有什么注册安全工程师证书"
    assert q1 == "某人在园区的某公司有什么某证书"
    mocked_replace_economic_zone.assert_awaited_once_with(q2)


def test_query_chat_should_send_placeholder_rewrite_prompt_with_qualification_constraints():
    capture_create = _CaptureCreate("某人在园区的某公司有什么某证书")
    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=capture_create))
    )
    chat = QueryChat(
        QueryChatConfig(api_key="k", base_url="http://x", model="m", timeout=10)
    )

    with patch.object(chat, "_get_client", return_value=fake_client):
        rewritten = chat.rewrite_query_remove_company(
            "张三在岱山化工园区的浙江远安流体设备有限公司有什么注册安全工程师证书"
        )

    assert rewritten == "某人在园区的某公司有什么某证书"
    system_prompt = capture_create.kwargs["messages"][0]["content"]
    assert "某公司" in system_prompt
    assert "某人" in system_prompt
    assert "某证书" in system_prompt
    assert "注册安全工程师证书" in system_prompt
    assert "特种设备操作证" in system_prompt


def test_query_chat_should_accept_placeholder_rewrite_and_emit_new_logs():
    source_query = "张三在园区的浙江远安流体设备有限公司有什么注册安全工程师证书"
    target_query = "某人在园区的某公司有什么某证书"
    chat = QueryChat(
        QueryChatConfig(api_key="k", base_url="http://x", model="m", timeout=10)
    )
    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **kwargs: SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content=target_query))]
                )
            )
        )
    )

    with patch("rag_stream.utils.query_chat.marker") as mocked_marker, patch.object(
        chat, "_get_client", return_value=fake_client
    ):
        result = chat.rewrite_query_remove_company(source_query)

    assert result == target_query
    mocked_marker.assert_any_call("query_chat.request_start", {"query_len": len(source_query)})
    mocked_marker.assert_any_call(
        "query_chat.request_complete",
        {"output_len": len(target_query), "normalized": True},
    )
