from __future__ import annotations

import sys
import types
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

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

    class _StubSqlPlus:
        @staticmethod
        def consume_last_execution_log():
            return []

    class _StubServer:
        def __init__(self):
            self.sqlFixed = _StubSqlFixed()
            self.sqlPlus = _StubSqlPlus()

        @staticmethod
        def get_sql_result(*args, **kwargs):
            return []

        @staticmethod
        def judgeQuery(*args, **kwargs):
            return []

    daishan_sql_stub.Server = _StubServer
    sys.modules["DaiShanSQL"] = daishan_sql_stub

from rag_stream.models.schemas import ChatRequest
from rag_stream.routes import chat_routes
from rag_stream.services import chat_general_service
from rag_stream.services.rag_service import stream_chat_response
from rag_stream.utils.session_manager import session_manager


@pytest.mark.asyncio
async def test_handle_chat_general_should_log_ragflow_intent_and_skip_daishansql_on_fallback():
    request = ChatRequest(question="测试问题", user_id="user-1", stream=True)
    chat_with_category = AsyncMock(return_value="ok")

    with patch.object(chat_general_service, "marker") as mocked_marker, patch.object(
        chat_general_service,
        "query_fixed_question_candidates",
        new=AsyncMock(return_value=[]),
    ):
        result = await chat_general_service.handle_chat_general(
            request=request,
            intent_service=object(),
            chat_with_category=chat_with_category,
        )

    assert result == "ok"
    mocked_marker.assert_any_call(
        "chat_general.ragflow_result",
        {
            "query_original": "测试问题",
            "query_q1": "测试问题",
            "query_q2": "测试问题",
            "table_name": chat_general_service.settings.intent.fixed_question_table_name,
            "candidate_count": 0,
            "top_candidates": [],
        },
    )
    decision_calls = [
        call for call in mocked_marker.call_args_list if call.args and call.args[0] == "chat_general.intent_decision"
    ]
    assert len(decision_calls) == 1
    assert decision_calls[0].args[1]["decision"] == "fallback"
    daishan_calls = [
        call for call in mocked_marker.call_args_list if call.args and call.args[0] == "chat_general.daishansql"
    ]
    assert len(daishan_calls) == 1
    assert daishan_calls[0].args[1]["called"] is False


@pytest.mark.asyncio
async def test_route_selected_fixed_question_should_log_daishansql_with_runtime_sql():
    request = ChatRequest(question="原问题", user_id="user-1", stream=True)
    chat_with_category = AsyncMock(return_value="ok")
    fake_server = SimpleNamespace(
        judgeQuery=Mock(return_value=[{"数据库查询结果": [[{"id": 1}]]}]),
        sqlPlus=SimpleNamespace(
            consume_last_execution_log=Mock(
                return_value=[{"sql_text": "SELECT 1", "result": [{"id": 1}], "error": ""}]
            )
        ),
    )

    with patch.object(chat_general_service, "marker") as mocked_marker, patch.object(
        chat_general_service, "_find_type3_prompt_by_question", return_value="前缀提示"
    ), patch.object(chat_general_service, "_get_server", return_value=fake_server), patch.object(
        chat_general_service.asyncio,
        "to_thread",
        new=AsyncMock(return_value=[{"数据库查询结果": [[{"id": 1}]]}]),
    ):
        result = await chat_general_service._route_selected_fixed_question(
            request=request,
            q2="归一化问题",
            selected_question="固定问题",
            chat_with_category=chat_with_category,
        )

    assert result == "ok"
    daishan_call = next(
        call for call in mocked_marker.call_args_list if call.args and call.args[0] == "chat_general.daishansql"
    )
    assert daishan_call.args[1]["called"] is True
    assert daishan_call.args[1]["method"] == "judgeQuery"
    assert daishan_call.args[1]["sql_text"] == ["SELECT 1"]


@pytest.mark.asyncio
async def test_chat_general_route_should_only_log_enter_event():
    request = ChatRequest(question="你好", user_id="user-1", stream=True)
    http_request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(intent_service=object())))

    with patch.object(chat_routes, "marker") as mocked_marker, patch.object(
        chat_routes, "handle_chat_general", new=AsyncMock(return_value="ok")
    ):
        result = await chat_routes.chat_general(request, http_request)

    assert result == "ok"
    mocked_marker.assert_called_once_with(
        "chat_general.enter",
        {
            "interface": "/api/general",
            "question": "你好",
            "has_user_id": True,
            "has_session_id": False,
            "stream": True,
        },
    )


class _FakeResponse:
    def __init__(self, chunks, status=200):
        self._chunks = chunks
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    @property
    def content(self):
        async def _iterator():
            for chunk in self._chunks:
                yield chunk

        return _iterator()

    async def text(self):
        return "error"


class _FakeClientSession:
    def __init__(self, response):
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def post(self, *args, **kwargs):
        return self._response


@pytest.mark.asyncio
async def test_stream_chat_response_should_log_chat_general_stream_end_once():
    session_id = "session-1"
    session_manager.sessions[session_id] = {
        "rag_session_id": "rag-session-1",
        "emit_chat_general_stream_log": True,
        "last_activity": "",
        "message_count": 0,
    }
    upstream = (
        'data: {"code":0,"data":{"answer":"你好","flag":1,"sessionId":"rag-session-1"}}\n\n'.encode("utf-8")
        + 'data: {"code":0,"data":true}\n\n'.encode("utf-8")
    )
    fake_response = _FakeResponse([upstream], status=200)

    with patch("rag_stream.services.rag_service.aiohttp.ClientSession", return_value=_FakeClientSession(fake_response)), patch(
        "rag_stream.services.rag_service.marker"
    ) as mocked_marker:
        output = []
        async for item in stream_chat_response("chat-1", "问题", session_id, "user-1"):
            output.append(item)

    assert output
    mocked_marker.assert_called_once()
    assert mocked_marker.call_args.args[0] == "chat_general.stream"
    assert mocked_marker.call_args.args[1]["phase"] == "end"
    assert mocked_marker.call_args.args[1]["status"] == "success"
