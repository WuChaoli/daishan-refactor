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

from src.models.schemas import ChatRequest
from src.services.chat_general_service import _route_with_sql_result, handle_chat_general


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
    asyncio.run(_test_handle_chat_general_should_fallback_to_general_when_intent_has_error())


async def _test_handle_chat_general_should_fallback_to_general_when_sql_result_empty():
    request = ChatRequest(question="查询安全信息", user_id="user-001", stream=True)

    intent_service = AsyncMock()
    intent_service.process_query.return_value = {
        "type": 2,
        "results": [],
    }

    chat_with_category = AsyncMock(return_value={"ok": True})

    with patch(
        "src.services.chat_general_service._post_process_type2",
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
    asyncio.run(_test_handle_chat_general_should_fallback_to_general_when_sql_result_empty())


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

    with patch(
        "src.services.chat_general_service.asyncio.to_thread",
        new=AsyncMock(return_value=sql_result),
    ) as mocked_to_thread:
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
        "园区安全负责人是谁\n\n"
        f"{str(sql_result)}\n\n"
        "东区的安全负责人是谁？"
    )
    assert routed_request.user_id == "user-001"
    assert routed_request.session_id == "session-001"
    assert routed_request.stream is False


def test_handle_chat_general_should_route_type3_with_combined_prompt():
    asyncio.run(_test_handle_chat_general_should_route_type3_with_combined_prompt())


async def _test_handle_chat_general_should_fallback_to_general_when_type3_answer_missing():
    request = ChatRequest(question="东区的安全负责人是谁？", user_id="user-001", stream=True)

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

    with patch(
        "src.services.chat_general_service.asyncio.to_thread",
        new=AsyncMock(),
    ) as mocked_to_thread:
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
    request = ChatRequest(question="东区的安全负责人是谁？", user_id="user-001", stream=True)

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

    with patch(
        "src.services.chat_general_service.asyncio.to_thread",
        new=AsyncMock(side_effect=RuntimeError("mock judge error")),
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
