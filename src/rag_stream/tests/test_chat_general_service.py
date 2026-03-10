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
from rag_stream.services.chat_general_service import (
    LOW_CONFIDENCE_REPLY,
    handle_chat_general,
)


async def _test_handle_chat_general_should_route_by_fixed_question_directly_when_similarity_is_0_7():
    request = ChatRequest(
        question="介绍一下岱山经开区情况",
        user_id="user-001",
        session_id="session-001",
        stream=False,
    )

    intent_service = AsyncMock()
    intent_service.query_fixed_question_candidates = AsyncMock(
        return_value=[
            {
                "question": "Question: 园区地址在哪\tAnswer: 园区地址信息",
                "similarity": 0.70,
            },
            {
                "question": "Question: 园区负责人是谁\tAnswer: 园区负责人信息",
                "similarity": 0.65,
            },
        ]
    )

    chat_with_category = AsyncMock(return_value={"ok": True})

    with (
        patch(
            "rag_stream.services.chat_general_service.replace_economic_zone",
            new=AsyncMock(return_value="介绍一下园区情况"),
        ),
        patch(
            "rag_stream.services.chat_general_service._find_type3_prompt_by_question",
            return_value="PROMPT",
        ),
        patch(
            "rag_stream.services.chat_general_service.asyncio.to_thread",
            new=AsyncMock(return_value={"rows": [{"name": "园区"}]}),
        ) as mocked_to_thread,
        patch(
            "rag_stream.services.chat_general_service.rerank_fixed_question_candidates",
            new=AsyncMock(return_value="园区负责人是谁"),
        ) as mocked_rerank,
    ):
        result = await handle_chat_general(
            request=request,
            intent_service=intent_service,
            chat_with_category=chat_with_category,
        )

    assert result == {"ok": True}
    intent_service.query_fixed_question_candidates.assert_awaited_once()
    query_arg = intent_service.query_fixed_question_candidates.await_args.args[0]
    assert query_arg == "介绍一下园区情况"

    mocked_rerank.assert_not_awaited()
    mocked_to_thread.assert_awaited_once()

    _, query2_arg, fixed_question_arg = mocked_to_thread.await_args.args
    assert query2_arg == "介绍一下园区情况"
    assert fixed_question_arg == "园区地址在哪"

    category_arg, routed_request = chat_with_category.await_args.args
    assert category_arg == "通用"
    assert routed_request.question.startswith("PROMPT\n\n")
    assert routed_request.question.endswith("\n\n介绍一下岱山经开区情况")


def test_handle_chat_general_should_route_by_fixed_question_directly_when_similarity_is_0_7():
    asyncio.run(
        _test_handle_chat_general_should_route_by_fixed_question_directly_when_similarity_is_0_7()
    )


async def _test_handle_chat_general_should_rerank_when_similarity_between_0_6_and_0_7_with_multi_candidates():
    request = ChatRequest(question="园区负责人电话是多少", user_id="user-002", stream=True)

    intent_service = AsyncMock()
    intent_service.query_fixed_question_candidates = AsyncMock(
        return_value=[
            {
                "question": "Question: 园区负责人是谁\tAnswer: 园区负责人信息",
                "similarity": 0.68,
            },
            {
                "question": "Question: 园区安全负责人是谁\tAnswer: 园区安全负责人信息",
                "similarity": 0.66,
            },
        ]
    )

    chat_with_category = AsyncMock(return_value={"ok": True})

    with (
        patch(
            "rag_stream.services.chat_general_service.replace_economic_zone",
            new=AsyncMock(return_value="园区负责人电话是多少"),
        ),
        patch(
            "rag_stream.services.chat_general_service.rerank_fixed_question_candidates",
            new=AsyncMock(return_value="园区安全负责人是谁"),
        ) as mocked_rerank,
        patch(
            "rag_stream.services.chat_general_service._find_type3_prompt_by_question",
            return_value="PROMPT",
        ),
        patch(
            "rag_stream.services.chat_general_service.asyncio.to_thread",
            new=AsyncMock(return_value=[{"ok": 1}]),
        ) as mocked_to_thread,
    ):
        await handle_chat_general(
            request=request,
            intent_service=intent_service,
            chat_with_category=chat_with_category,
        )

    mocked_rerank.assert_awaited_once()
    _, _, selected_question = mocked_to_thread.await_args.args
    assert selected_question == "园区安全负责人是谁"


def test_handle_chat_general_should_rerank_when_similarity_between_0_6_and_0_7_with_multi_candidates():
    asyncio.run(
        _test_handle_chat_general_should_rerank_when_similarity_between_0_6_and_0_7_with_multi_candidates()
    )


async def _test_handle_chat_general_should_fallback_to_general_reply_when_similarity_is_below_threshold():
    request = ChatRequest(question="随便聊聊", user_id="user-003", session_id="session-003", stream=False)

    intent_service = AsyncMock()
    intent_service.query_fixed_question_candidates = AsyncMock(
        return_value=[
            {
                "question": "Question: 园区地址在哪\tAnswer: 园区地址信息",
                "similarity": 0.59,
            }
        ]
    )

    chat_with_category = AsyncMock(return_value={"ok": True})

    with patch(
        "rag_stream.services.chat_general_service.replace_economic_zone",
        new=AsyncMock(return_value="随便聊聊"),
    ):
        result = await handle_chat_general(
            request=request,
            intent_service=intent_service,
            chat_with_category=chat_with_category,
        )

    assert result == {"ok": True}
    category_arg, routed_request = chat_with_category.await_args.args
    assert category_arg == "通用"
    assert routed_request.question == LOW_CONFIDENCE_REPLY
    assert routed_request.user_id == "user-003"
    assert routed_request.session_id == "session-003"


def test_handle_chat_general_should_fallback_to_general_reply_when_similarity_is_below_threshold():
    asyncio.run(
        _test_handle_chat_general_should_fallback_to_general_reply_when_similarity_is_below_threshold()
    )
