from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from rag_stream.services.guess_questions_service import handle_guess_questions, process_type2


async def _test_handle_guess_questions_should_call_general_chat_when_type2_results_empty():
    intent_service = AsyncMock()
    intent_service.process_query.return_value = {
        "type": 2,
        "query": "园区最近安全态势怎么样",
        "results": [],
    }

    general_client = Mock()
    general_client.run_chat.return_value = SimpleNamespace(
        answer='["园区本周有哪些安全风险？", "近三天是否有告警事件？", "重点企业安全状态如何？"]'
    )

    with patch(
        "rag_stream.services.guess_questions_service.get_client",
        return_value=general_client,
    ) as mock_get_client:
        result = await handle_guess_questions("园区最近安全态势怎么样", intent_service)

    assert result == [
        {"question": "园区本周有哪些安全风险？"},
        {"question": "近三天是否有告警事件？"},
        {"question": "重点企业安全状态如何？"},
    ]
    mock_get_client.assert_called_once_with("GENRAL_CHAT")
    assert general_client.run_chat.call_count == 1


def test_handle_guess_questions_should_call_general_chat_when_type2_results_empty():
    asyncio.run(_test_handle_guess_questions_should_call_general_chat_when_type2_results_empty())


async def _test_handle_guess_questions_should_return_empty_when_general_chat_unavailable():
    intent_service = AsyncMock()
    intent_service.process_query.return_value = {
        "type": 2,
        "query": "园区最近安全态势怎么样",
        "results": [],
    }

    with patch(
        "rag_stream.services.guess_questions_service.get_client",
        side_effect=ValueError("missing GENRAL_CHAT client"),
    ):
        result = await handle_guess_questions("园区最近安全态势怎么样", intent_service)

    assert result == []


def test_handle_guess_questions_should_return_empty_when_general_chat_unavailable():
    asyncio.run(_test_handle_guess_questions_should_return_empty_when_general_chat_unavailable())


def test_process_type2_should_keep_empty_result_contract_when_results_empty():
    intent_result = {
        "type": 2,
        "results": [],
    }

    assert process_type2(intent_result) == []
