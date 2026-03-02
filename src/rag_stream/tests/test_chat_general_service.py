from __future__ import annotations

import asyncio
import sys
import types
from unittest.mock import AsyncMock, patch

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

from rag_stream.models.schemas import ChatRequest
from rag_stream.services import chat_general_service
from rag_stream.services.chat_general_service import (
    _route_with_sql_result,
    handle_chat_general,
    replace_economic_zone,
)


async def _test_route_with_sql_result_should_keep_original_request_fields():
    captured: dict[str, ChatRequest | str] = {}

    async def fake_chat_with_category(category: str, request: ChatRequest):
        captured["category"] = category
        captured["request"] = request
        return {"ok": True}

    source_request = ChatRequest(
        question="园区安全态势",
        session_id="session-001",
        user_id="user-001",
        stream=False,
    )

    await _route_with_sql_result(
        request=source_request,
        sql_result="{" + '"risk": "low"' + "}",
        target_category="通用",
        chat_with_category=fake_chat_with_category,
    )

    routed_request = captured["request"]
    assert isinstance(routed_request, ChatRequest)
    assert captured["category"] == "通用"
    assert routed_request.user_id == "user-001"
    assert routed_request.session_id == "session-001"
    assert routed_request.stream is False


def test_route_with_sql_result_should_keep_original_request_fields():
    asyncio.run(_test_route_with_sql_result_should_keep_original_request_fields())


async def _test_handle_chat_general_should_fallback_to_general_when_intent_has_error():
    request = ChatRequest(question="你好", user_id="user-001", stream=True)

    intent_service = AsyncMock()
    intent_service.process_query.return_value = {
        "type": 0,
        "data": {"error": "intent service unavailable"},
    }

    chat_with_category = AsyncMock(return_value={"ok": True})

    result = await handle_chat_general(
        request=request,
        intent_service=intent_service,
        chat_with_category=chat_with_category,
    )

    assert result == {"ok": True}
    chat_with_category.assert_awaited_once_with("通用", request)


def test_handle_chat_general_should_fallback_to_general_when_intent_has_error():
    asyncio.run(
        _test_handle_chat_general_should_fallback_to_general_when_intent_has_error()
    )


async def _test_handle_chat_general_should_fallback_to_general_when_sql_result_empty():
    request = ChatRequest(question="查询安全信息", user_id="user-001", stream=True)

    intent_service = AsyncMock()
    intent_service.process_query.return_value = {
        "type": 2,
        "results": [],
    }

    chat_with_category = AsyncMock(return_value={"ok": True})

    with patch(
        "rag_stream.services.chat_general_service._post_process_type2",
        new=AsyncMock(return_value={"type": 2, "data": {"sql_result": ""}}),
    ):
        result = await handle_chat_general(
            request=request,
            intent_service=intent_service,
            chat_with_category=chat_with_category,
        )

    assert result == {"ok": True}
    chat_with_category.assert_awaited_once_with("通用", request)


def test_handle_chat_general_should_fallback_to_general_when_sql_result_empty():
    asyncio.run(
        _test_handle_chat_general_should_fallback_to_general_when_sql_result_empty()
    )


async def _test_handle_chat_general_should_route_type3_with_combined_prompt():
    request = ChatRequest(
        question="东区的安全负责人是谁？",
        user_id="user-001",
        session_id="session-001",
        stream=False,
    )

    intent_service = AsyncMock()
    intent_service.process_query.return_value = {
        "type": 3,
        "answer": "园区安全负责人是谁",
        "results": [
            {
                "question": "Question: 东区的安全负责人是谁？\tAnswer: 园区安全负责人是谁",
                "similarity": 0.93,
            }
        ],
    }

    sql_result = [
        {
            "问题": "东区的安全负责人是谁？",
            "数据库查询结果": [[{"园区名称": "东区", "安全负责人姓名": "刘天"}]],
        }
    ]

    chat_with_category = AsyncMock(return_value={"ok": True})
    mapped_prompt = "请你按照模板回答园区安全负责人信息。"

    with (
        patch(
            "rag_stream.services.chat_general_service.replace_economic_zone",
            new=AsyncMock(return_value=request.question),
        ),
        patch(
            "rag_stream.services.chat_general_service._find_type3_prompt_by_question",
            return_value=mapped_prompt,
        ),
        patch(
            "rag_stream.services.chat_general_service.asyncio.to_thread",
            new=AsyncMock(return_value=sql_result),
        ) as mocked_to_thread,
    ):
        result = await handle_chat_general(
            request=request,
            intent_service=intent_service,
            chat_with_category=chat_with_category,
        )

    assert result == {"ok": True}
    mocked_to_thread.assert_awaited_once()
    fn_arg, query_arg, return_question_arg = mocked_to_thread.await_args.args
    assert getattr(fn_arg, "__name__", "") == "judgeQuery"
    assert query_arg == "东区的安全负责人是谁？"
    assert return_question_arg == "东区的安全负责人是谁？"
    chat_with_category.assert_awaited_once()

    category_arg, routed_request = chat_with_category.await_args.args
    assert category_arg == "通用"
    assert isinstance(routed_request, ChatRequest)
    assert routed_request.question == (
        f"{mapped_prompt}\n\n{str(sql_result)}\n\n东区的安全负责人是谁？"
    )
    assert routed_request.user_id == "user-001"
    assert routed_request.session_id == "session-001"
    assert routed_request.stream is False


def test_handle_chat_general_should_route_type3_with_combined_prompt():
    asyncio.run(_test_handle_chat_general_should_route_type3_with_combined_prompt())


async def _test_handle_chat_general_should_fallback_to_general_when_type3_answer_missing():
    request = ChatRequest(
        question="东区的安全负责人是谁？", user_id="user-001", stream=True
    )

    intent_service = AsyncMock()
    intent_service.process_query.return_value = {
        "type": 3,
        "answer": "",
        "results": [
            {
                "question": "Question: 东区的安全负责人是谁？\tAnswer: 园区安全负责人是谁",
                "similarity": 0.93,
            }
        ],
    }

    chat_with_category = AsyncMock(return_value={"ok": True})

    with (
        patch(
            "rag_stream.services.chat_general_service.replace_economic_zone",
            new=AsyncMock(return_value=request.question),
        ),
        patch(
            "rag_stream.services.chat_general_service.asyncio.to_thread",
            new=AsyncMock(),
        ) as mocked_to_thread,
    ):
        result = await handle_chat_general(
            request=request,
            intent_service=intent_service,
            chat_with_category=chat_with_category,
        )

    assert result == {"ok": True}
    mocked_to_thread.assert_not_called()
    chat_with_category.assert_awaited_once_with("通用", request)


def test_handle_chat_general_should_fallback_to_general_when_type3_answer_missing():
    asyncio.run(
        _test_handle_chat_general_should_fallback_to_general_when_type3_answer_missing()
    )


async def _test_handle_chat_general_should_fallback_to_general_when_type3_judgequery_raise():
    request = ChatRequest(
        question="东区的安全负责人是谁？", user_id="user-001", stream=True
    )

    intent_service = AsyncMock()
    intent_service.process_query.return_value = {
        "type": 3,
        "answer": "园区安全负责人是谁",
        "results": [
            {
                "question": "Question: 东区的安全负责人是谁？\tAnswer: 园区安全负责人是谁",
                "similarity": 0.93,
            }
        ],
    }

    chat_with_category = AsyncMock(return_value={"ok": True})

    with (
        patch(
            "rag_stream.services.chat_general_service.replace_economic_zone",
            new=AsyncMock(return_value=request.question),
        ),
        patch(
            "rag_stream.services.chat_general_service.asyncio.to_thread",
            new=AsyncMock(side_effect=RuntimeError("mock judge error")),
        ),
    ):
        result = await handle_chat_general(
            request=request,
            intent_service=intent_service,
            chat_with_category=chat_with_category,
        )

    assert result == {"ok": True}
    chat_with_category.assert_awaited_once_with("通用", request)


def test_handle_chat_general_should_fallback_to_general_when_type3_judgequery_raise():
    asyncio.run(
        _test_handle_chat_general_should_fallback_to_general_when_type3_judgequery_raise()
    )


async def _test_handle_chat_general_should_use_ai_rewrite_before_intent():
    request = ChatRequest(
        question="介绍一下浙江世倍尔新材料有限公司在园区的情况",
        user_id="user-001",
        stream=True,
    )

    intent_service = AsyncMock()
    intent_service.process_query.return_value = {
        "type": 0,
        "data": {"error": "intent service unavailable"},
    }

    chat_with_category = AsyncMock(return_value={"ok": True})

    with patch(
        "src.services.chat_general_service.asyncio.to_thread",
        new=AsyncMock(return_value="介绍一下在园区的情况"),
    ) as mocked_to_thread:
        result = await handle_chat_general(
            request=request,
            intent_service=intent_service,
            chat_with_category=chat_with_category,
        )

    assert result == {"ok": True}
    mocked_to_thread.assert_awaited_once()
    intent_service.process_query.assert_awaited_once_with(
        "介绍一下在园区的情况", "user-001"
    )
    assert request.question == "介绍一下浙江世倍尔新材料有限公司在园区的情况"


def test_handle_chat_general_should_use_ai_rewrite_before_intent():
    asyncio.run(_test_handle_chat_general_should_use_ai_rewrite_before_intent())


async def _test_handle_chat_general_should_keep_original_query_when_ai_rewrite_fails():
    request = ChatRequest(
        question="岱山经济开发区浙江世倍尔新材料有限公司安全吗",
        user_id="user-001",
        stream=True,
    )

    intent_service = AsyncMock()
    intent_service.process_query.return_value = {
        "type": 0,
        "data": {"error": "intent service unavailable"},
    }

    chat_with_category = AsyncMock(return_value={"ok": True})

    with patch(
        "src.services.chat_general_service.asyncio.to_thread",
        new=AsyncMock(side_effect=RuntimeError("mock rewrite failure")),
    ) as mocked_to_thread:
        result = await handle_chat_general(
            request=request,
            intent_service=intent_service,
            chat_with_category=chat_with_category,
        )

    assert result == {"ok": True}
    mocked_to_thread.assert_awaited_once()
    intent_service.process_query.assert_awaited_once_with(
        "岱山经济开发区浙江世倍尔新材料有限公司安全吗",
        "user-001",
    )
    assert request.question == "岱山经济开发区浙江世倍尔新材料有限公司安全吗"


def test_handle_chat_general_should_keep_original_query_when_ai_rewrite_fails():
    asyncio.run(
        _test_handle_chat_general_should_keep_original_query_when_ai_rewrite_fails()
    )


async def _test_replace_economic_zone_should_log_skip_when_no_company_keyword():
    query = "今天园区天气怎么样"
    with (
        patch("src.services.chat_general_service.marker") as mocked_marker,
        patch(
            "src.services.chat_general_service.asyncio.to_thread",
            new=AsyncMock(return_value="unused"),
        ) as mocked_to_thread,
    ):
        result = await replace_economic_zone(query)

    assert result == query
    mocked_to_thread.assert_not_awaited()
    mocked_marker.assert_any_call(
        "query_normalized_skip_non_company", {"query_len": len(query)}
    )


def test_replace_economic_zone_should_log_skip_when_no_company_keyword():
    asyncio.run(_test_replace_economic_zone_should_log_skip_when_no_company_keyword())


async def _test_replace_economic_zone_should_fallback_when_disabled():
    query = "浙江世倍尔新材料有限公司现在怎么样"
    with (
        patch(
            "src.services.chat_general_service.settings.query_chat.enabled",
            new=False,
        ),
        patch("src.services.chat_general_service.marker") as mocked_marker,
        patch(
            "src.services.chat_general_service.asyncio.to_thread",
            new=AsyncMock(return_value="unused"),
        ) as mocked_to_thread,
    ):
        result = await replace_economic_zone(query)

    assert result == query
    mocked_to_thread.assert_not_awaited()
    mocked_marker.assert_any_call(
        "query_normalized_disabled", {"query_len": len(query)}
    )


def test_replace_economic_zone_should_fallback_when_disabled():
    asyncio.run(_test_replace_economic_zone_should_fallback_when_disabled())


async def _test_replace_economic_zone_should_fallback_when_misconfigured():
    query = "浙江世倍尔新材料有限公司现在怎么样"
    with (
        patch(
            "src.services.chat_general_service.settings.query_chat.enabled",
            new=True,
        ),
        patch(
            "src.services.chat_general_service.settings.query_chat.api_key",
            new="",
        ),
        patch(
            "src.services.chat_general_service.settings.query_chat.base_url",
            new="",
        ),
        patch("src.services.chat_general_service.marker") as mocked_marker,
        patch(
            "src.services.chat_general_service.asyncio.to_thread",
            new=AsyncMock(return_value="unused"),
        ) as mocked_to_thread,
    ):
        result = await replace_economic_zone(query)

    assert result == query
    mocked_to_thread.assert_not_awaited()
    mocked_marker.assert_any_call(
        "query_normalized_misconfigured",
        {"query_len": len(query)},
    )


def test_replace_economic_zone_should_fallback_when_misconfigured():
    asyncio.run(_test_replace_economic_zone_should_fallback_when_misconfigured())


async def _test_replace_economic_zone_should_log_start_and_success():
    query = "浙江世倍尔新材料有限公司现在怎么样"
    rewritten = "现在怎么样"
    with (
        patch("src.services.chat_general_service.marker") as mocked_marker,
        patch(
            "src.services.chat_general_service.asyncio.to_thread",
            new=AsyncMock(return_value=rewritten),
        ) as mocked_to_thread,
    ):
        result = await replace_economic_zone(query)

    assert result == rewritten
    mocked_to_thread.assert_awaited_once()
    mocked_marker.assert_any_call("query_normalized_start", {"query_len": len(query)})
    mocked_marker.assert_any_call("query_normalized", {"normalized": True})


def test_replace_economic_zone_should_log_start_and_success():
    asyncio.run(_test_replace_economic_zone_should_log_start_and_success())


async def _test_replace_economic_zone_should_log_failure_and_fallback():
    """AI 异常时回退原句 - 异常在 rewrite_query 内部捕获"""
    query = "浙江世倍尔新材料有限公司现在怎么样"
    with (
        patch("src.services.chat_general_service.marker") as mocked_marker,
        patch(
            "src.services.chat_general_service.asyncio.to_thread",
            new=AsyncMock(side_effect=RuntimeError("mock ai error")),
        ),
    ):
        result = await replace_economic_zone(query)

    assert result == query
    mocked_marker.assert_any_call("query_normalized_start", {"query_len": len(query)})
    # rewrite_query 内部捕获异常并返回原 query，不会抛出到 replace_economic_zone
    # 因此会记录 query_normalized 而不是 query_normalized_failed
    mocked_marker.assert_any_call("query_normalized", {"normalized": False})


def test_replace_economic_zone_should_log_failure_and_fallback():
    asyncio.run(_test_replace_economic_zone_should_log_failure_and_fallback())


async def _test_replace_economic_zone_success():
    """TEST-01: AI 改写成功路径测试"""
    query = "某某公司安全情况查询"
    expected_rewritten = "查询安全情况"

    with (
        patch("src.services.chat_general_service.marker") as mocked_marker,
        patch(
            "src.services.chat_general_service.asyncio.to_thread",
            new=AsyncMock(return_value=expected_rewritten),
        ) as mocked_to_thread,
    ):
        result = await replace_economic_zone(query)

    assert result == expected_rewritten
    mocked_to_thread.assert_awaited_once()
    # Verify the call used correct arguments
    call_args = mocked_to_thread.await_args
    assert call_args.args[0].__name__ == "rewrite_query_remove_company"
    assert call_args.args[1] == query
    # Verify success logging
    mocked_marker.assert_any_call("query_normalized_start", {"query_len": len(query)})
    mocked_marker.assert_any_call("query_normalized", {"normalized": True})


def test_replace_economic_zone_success():
    asyncio.run(_test_replace_economic_zone_success())


async def _test_replace_economic_zone_api_error_fallback():
    """TEST-02: AI API 异常时回退原句"""
    query = "某某公司安全情况查询"

    with (
        patch("src.services.chat_general_service.marker") as mocked_marker,
        patch(
            "src.services.chat_general_service.asyncio.to_thread",
            new=AsyncMock(side_effect=RuntimeError("API timeout")),
        ),
    ):
        result = await replace_economic_zone(query)

    # 验证返回原 query（降级）
    assert result == query
    # 异常在 rewrite_query 内部捕获并返回原 query，不会记录 query_normalized_failed
    mocked_marker.assert_any_call("query_normalized_start", {"query_len": len(query)})
    mocked_marker.assert_any_call("query_normalized", {"normalized": False})


def test_replace_economic_zone_api_error_fallback():
    asyncio.run(_test_replace_economic_zone_api_error_fallback())


async def _test_replace_economic_zone_empty_response_fallback():
    """TEST-02: AI 返回空值时回退原句"""
    query = "某某公司安全情况查询"

    with (
        patch("src.services.chat_general_service.marker") as mocked_marker,
        patch(
            "src.services.chat_general_service.asyncio.to_thread",
            new=AsyncMock(return_value=""),
        ),
    ):
        result = await replace_economic_zone(query)

    # 验证返回原 query
    assert result == query
    # Verify empty response logging
    mocked_marker.assert_any_call("query_normalized_empty", {}, level="WARNING")


def test_replace_economic_zone_empty_response_fallback():
    asyncio.run(_test_replace_economic_zone_empty_response_fallback())


async def _test_replace_economic_zone_disabled_fallback():
    """TEST-02: 配置禁用时直接返回原句"""
    query = "某某公司安全情况查询"

    with (
        patch(
            "src.services.chat_general_service.settings.query_chat.enabled",
            new=False,
        ),
        patch("src.services.chat_general_service.marker") as mocked_marker,
        patch(
            "src.services.chat_general_service.asyncio.to_thread",
            new=AsyncMock(return_value="unused"),
        ) as mocked_to_thread,
    ):
        result = await replace_economic_zone(query)

    # 验证返回原 query
    assert result == query
    # 不调用 AI
    mocked_to_thread.assert_not_awaited()
    # Verify disabled logging
    mocked_marker.assert_any_call(
        "query_normalized_disabled", {"query_len": len(query)}
    )


def test_replace_economic_zone_disabled_fallback():
    asyncio.run(_test_replace_economic_zone_disabled_fallback())


async def _test_handle_chat_general_should_route_type1_when_mapping_hit():
    request = ChatRequest(
        question="介绍园区情况",
        user_id="user-001",
        session_id="session-001",
        stream=False,
    )

    intent_service = AsyncMock()
    intent_service.process_query.return_value = {
        "type": 1,
        "results": [
            {
                "question": "Question: 园区整体情况\tAnswer: global+parkIntro [knowledgebase:园区知识库]",
                "similarity": 0.81,
            }
        ],
    }

    chat_with_category = AsyncMock(return_value={"ok": True})

    with (
        patch(
            "rag_stream.services.chat_general_service.replace_economic_zone",
            new=AsyncMock(return_value=request.question),
        ),
        patch(
            "rag_stream.services.chat_general_service._find_type1_mapping_by_question",
            return_value="TYPE1_PROMPT",
        ) as mocked_lookup,
    ):
        result = await handle_chat_general(
            request=request,
            intent_service=intent_service,
            chat_with_category=chat_with_category,
        )

    assert result == {"ok": True}
    mocked_lookup.assert_called_once_with("园区整体情况")
    category_arg, routed_request = chat_with_category.await_args.args
    assert category_arg == "园区知识库"
    assert routed_request.question == "TYPE1_PROMPT\n\n介绍园区情况\n\n1"


def test_handle_chat_general_should_route_type1_when_mapping_hit():
    asyncio.run(_test_handle_chat_general_should_route_type1_when_mapping_hit())


async def _test_handle_chat_general_should_fallback_general_when_type1_mapping_miss():
    request = ChatRequest(question="介绍园区情况", user_id="user-001", stream=True)

    intent_service = AsyncMock()
    intent_service.process_query.return_value = {
        "type": 1,
        "results": [
            {
                "question": "Question: 园区整体情况\tAnswer: global+parkIntro [knowledgebase:园区知识库]",
                "similarity": 0.81,
            }
        ],
    }

    chat_with_category = AsyncMock(return_value={"ok": True})

    with (
        patch(
            "rag_stream.services.chat_general_service.replace_economic_zone",
            new=AsyncMock(return_value=request.question),
        ),
        patch(
            "rag_stream.services.chat_general_service._find_type1_mapping_by_question",
            return_value="",
        ),
        patch(
            "rag_stream.services.chat_general_service._post_process_type1",
            new=AsyncMock(),
        ) as mocked_post_type1,
    ):
        result = await handle_chat_general(
            request=request,
            intent_service=intent_service,
            chat_with_category=chat_with_category,
        )

    assert result == {"ok": True}
    mocked_post_type1.assert_not_awaited()
    chat_with_category.assert_awaited_once_with("通用", request)


def test_handle_chat_general_should_fallback_general_when_type1_mapping_miss():
    asyncio.run(_test_handle_chat_general_should_fallback_general_when_type1_mapping_miss())


async def _test_handle_chat_general_should_route_type2_when_mapping_hit():
    request = ChatRequest(
        question="查询重点监管危化品",
        user_id="user-001",
        session_id="session-002",
        stream=False,
    )

    intent_service = AsyncMock()
    intent_service.process_query.return_value = {
        "type": 2,
        "results": [
            {
                "question": "Question: 园区有哪些重点监管危化品\tAnswer: v_ai_ipark_enterprise_key_chemicals",
                "similarity": 0.77,
            }
        ],
    }

    chat_with_category = AsyncMock(return_value={"ok": True})
    sql_result = {"rows": [{"name": "甲类危化品"}]}

    with (
        patch(
            "rag_stream.services.chat_general_service.replace_economic_zone",
            new=AsyncMock(return_value=request.question),
        ),
        patch(
            "rag_stream.services.chat_general_service._find_type2_mapping_by_question",
            return_value="TYPE2_PROMPT",
        ) as mocked_lookup,
        patch(
            "rag_stream.services.chat_general_service.asyncio.to_thread",
            new=AsyncMock(return_value=sql_result),
        ) as mocked_to_thread,
    ):
        result = await handle_chat_general(
            request=request,
            intent_service=intent_service,
            chat_with_category=chat_with_category,
        )

    assert result == {"ok": True}
    mocked_lookup.assert_called_once_with("园区有哪些重点监管危化品")
    mocked_to_thread.assert_awaited_once()
    category_arg, routed_request = chat_with_category.await_args.args
    assert category_arg == "通用"
    assert routed_request.question.startswith("TYPE2_PROMPT\n\n查询重点监管危化品\n\n")
    assert routed_request.question.endswith(str(sql_result))


def test_handle_chat_general_should_route_type2_when_mapping_hit():
    asyncio.run(_test_handle_chat_general_should_route_type2_when_mapping_hit())


async def _test_handle_chat_general_should_fallback_general_when_type2_mapping_miss():
    request = ChatRequest(question="查询重点监管危化品", user_id="user-001", stream=True)

    intent_service = AsyncMock()
    intent_service.process_query.return_value = {
        "type": 2,
        "results": [
            {
                "question": "Question: 园区有哪些重点监管危化品\tAnswer: v_ai_ipark_enterprise_key_chemicals",
                "similarity": 0.77,
            }
        ],
    }

    chat_with_category = AsyncMock(return_value={"ok": True})

    with (
        patch(
            "rag_stream.services.chat_general_service.replace_economic_zone",
            new=AsyncMock(return_value=request.question),
        ),
        patch(
            "rag_stream.services.chat_general_service._find_type2_mapping_by_question",
            return_value="",
        ),
        patch(
            "rag_stream.services.chat_general_service._post_process_type2",
            new=AsyncMock(),
        ) as mocked_post_type2,
    ):
        result = await handle_chat_general(
            request=request,
            intent_service=intent_service,
            chat_with_category=chat_with_category,
        )

    assert result == {"ok": True}
    mocked_post_type2.assert_not_awaited()
    chat_with_category.assert_awaited_once_with("通用", request)


def test_handle_chat_general_should_fallback_general_when_type2_mapping_miss():
    asyncio.run(_test_handle_chat_general_should_fallback_general_when_type2_mapping_miss())


def test_find_type1_mapping_should_warn_when_mapping_file_missing(tmp_path):
    missing_path = tmp_path / "type1_question_mapping.json"
    assert not missing_path.exists()

    with (
        patch.object(chat_general_service, "_TYPE1_PROMPT_MAPPING_PATH", missing_path),
        patch.object(chat_general_service, "marker") as mocked_marker,
    ):
        chat_general_service._clear_prompt_mapping_cache()
        prompt = chat_general_service._find_type1_mapping_by_question("园区整体情况")

    assert prompt == ""
    names = [call.args[0] for call in mocked_marker.call_args_list if call.args]
    assert "type1.prompt_mapping_missing" in names
    assert "type1.prompt_mapping_lookup" in names


def test_find_type2_mapping_should_warn_when_mapping_file_corrupted(tmp_path):
    mapping_path = tmp_path / "type2_question_mapping.json"
    mapping_path.write_text("{invalid_json", encoding="utf-8")

    with (
        patch.object(chat_general_service, "_TYPE2_PROMPT_MAPPING_PATH", mapping_path),
        patch.object(chat_general_service, "marker") as mocked_marker,
    ):
        chat_general_service._clear_prompt_mapping_cache()
        prompt = chat_general_service._find_type2_mapping_by_question("园区有哪些重点监管危化品")

    assert prompt == ""
    names = [call.args[0] for call in mocked_marker.call_args_list if call.args]
    assert "type2.prompt_mapping_load_failed" in names
    assert "type2.prompt_mapping_lookup" in names
