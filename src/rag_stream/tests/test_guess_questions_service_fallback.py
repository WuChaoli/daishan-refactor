from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from rag_stream.services.guess_questions_service import handle_guess_questions


async def _test_handle_guess_questions_should_return_fixed_question_candidates_with_same_output_shape():
    intent_service = AsyncMock()
    intent_service.query_fixed_question_candidates = AsyncMock(
        return_value=[
            {
                "question": "Question: 园区地址在哪\tAnswer: 园区地址信息",
                "similarity": 0.88,
            },
            {
                "question": "Question: 园区负责人是谁\tAnswer: 园区负责人信息",
                "similarity": 0.66,
            },
            {
                "question": "Question: 园区安全负责人是谁\tAnswer: 园区安全负责人信息",
                "similarity": 0.61,
            },
            {
                "question": "Question: 园区有哪些企业\tAnswer: 园区企业信息",
                "similarity": 0.55,
            },
        ]
    )

    with patch(
        "rag_stream.services.guess_questions_service._rewrite_query_remove_company_with_fallback",
        new=AsyncMock(return_value="园区有哪些企业"),
    ):
        result = await handle_guess_questions("岱山经开区有哪些企业", intent_service)

    assert result == [
        {"question": "园区地址在哪"},
        {"question": "园区负责人是谁"},
        {"question": "园区安全负责人是谁"},
    ]


def test_handle_guess_questions_should_return_fixed_question_candidates_with_same_output_shape():
    asyncio.run(
        _test_handle_guess_questions_should_return_fixed_question_candidates_with_same_output_shape()
    )


async def _test_handle_guess_questions_should_call_general_chat_when_no_fixed_candidates():
    intent_service = AsyncMock()
    intent_service.query_fixed_question_candidates = AsyncMock(return_value=[])

    general_client = Mock()
    general_client.run_chat.return_value = SimpleNamespace(
        answer='["园区本周有哪些安全风险？", "近三天是否有告警事件？", "重点企业安全状态如何？"]'
    )

    with (
        patch(
            "rag_stream.services.guess_questions_service._rewrite_query_remove_company_with_fallback",
            new=AsyncMock(return_value="园区最近安全态势怎么样"),
        ),
        patch(
            "rag_stream.services.guess_questions_service.get_client",
            return_value=general_client,
        ) as mock_get_client,
    ):
        result = await handle_guess_questions("园区最近安全态势怎么样", intent_service)

    assert result == [
        {"question": "园区本周有哪些安全风险？"},
        {"question": "近三天是否有告警事件？"},
        {"question": "重点企业安全状态如何？"},
    ]
    mock_get_client.assert_called_once_with("GENRAL_CHAT")
    assert general_client.run_chat.call_count == 1


def test_handle_guess_questions_should_call_general_chat_when_no_fixed_candidates():
    asyncio.run(_test_handle_guess_questions_should_call_general_chat_when_no_fixed_candidates())
