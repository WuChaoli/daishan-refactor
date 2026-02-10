from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

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
