import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# 添加 rag_stream 目录到 Python 路径，确保可以 import src.*
rag_stream_path = Path(__file__).parent.parent
sys.path.insert(0, str(rag_stream_path))

from src.services.rag_service import stream_chat_response


class _FakeContent:
    def __init__(self, chunks):
        self._chunks = list(chunks)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._chunks:
            raise StopAsyncIteration
        return self._chunks.pop(0)


class _FakeResponse:
    def __init__(self, chunks, status=200):
        self.status = status
        self.content = _FakeContent(chunks)

    async def text(self):
        return ""


class _FakePostCtx:
    def __init__(self, response):
        self._response = response

    async def __aenter__(self):
        return self._response

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeClientSession:
    def __init__(self, response):
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def post(self, *args, **kwargs):
        return _FakePostCtx(self._response)


@pytest.mark.asyncio
async def test_stream_chat_response_end_chunk_only_once():
    # 先输出一段 answer，再输出 data=true 表示结束；结束后即使上游还有内容，也不应再输出任何 chunk。
    upstream = (
        b'data: {"code": 0, "data": {"answer": "hello"}}\n\n'
        b'data: {"code": 0, "data": true}\n\n'
        b'data: {"code": 0, "data": {"answer": "SHOULD_NOT_SEE"}}\n\n'
    )
    fake_response = _FakeResponse([upstream], status=200)

    with patch("src.services.rag_service.aiohttp.ClientSession", return_value=_FakeClientSession(fake_response)):
        events = []
        async for sse in stream_chat_response("chat_id", "question", "session_id"):
            assert sse.startswith("data: ")
            payload = json.loads(sse.split("data: ", 1)[1])
            events.append(payload)

    end_events = [e for e in events if e.get("data", {}).get("end") == 1]
    assert len(end_events) == 1

    answers = [e.get("data", {}).get("answer") for e in events if e.get("data", {}).get("flag") == 1]
    assert "SHOULD_NOT_SEE" not in answers


@pytest.mark.asyncio
async def test_stream_chat_response_ignores_non_prefix_update_to_avoid_duplicate_tail():
    # 模拟“第二次返回对历史内容做插入/改写”，不是简单的前缀追加：
    # old = "abcXYZ"
    # new = "abc123XYZ"（插入在中间）
    # 这种更新无法用 append-only 的方式表达，服务端应忽略以避免重复输出尾部 "XYZ"。
    upstream = (
        b'data: {"code": 0, "data": {"answer": "abcXYZ"}}\n\n'
        b'data: {"code": 0, "data": {"answer": "abc123XYZ"}}\n\n'
        b'data: {"code": 0, "data": true}\n\n'
    )
    fake_response = _FakeResponse([upstream], status=200)

    with patch("src.services.rag_service.aiohttp.ClientSession", return_value=_FakeClientSession(fake_response)):
        answers = []
        async for sse in stream_chat_response("chat_id", "question", "session_id"):
            payload = json.loads(sse.split("data: ", 1)[1])
            if payload.get("data", {}).get("flag") == 1:
                answers.append(payload["data"]["answer"])

    # 只应输出第一次的完整内容；第二次非前缀更新应被忽略
    assert answers == ["abcXYZ"]


@pytest.mark.asyncio
async def test_stream_chat_response_ignores_final_full_rewrite_with_inserted_markers():
    # 贴近线上现象：最后一条会“全量改写”，在中间插入 ##x$$ 标记。
    # 服务端应忽略这类非前缀更新，避免前端看到最后一次把全量再输出一遍。
    upstream = (
        b'data: {"code": 0, "data": {"answer": "hello\\nworld"}}\n\n'
        b'data: {"code": 0, "data": {"answer": "hello\\nworld ##1$$"}}\n\n'
        b'data: {"code": 0, "data": true}\n\n'
    )
    fake_response = _FakeResponse([upstream], status=200)

    with patch("src.services.rag_service.aiohttp.ClientSession", return_value=_FakeClientSession(fake_response)):
        answers = []
        async for sse in stream_chat_response("chat_id", "question", "session_id"):
            payload = json.loads(sse.split("data: ", 1)[1])
            if payload.get("data", {}).get("flag") == 1:
                answers.append(payload["data"]["answer"])

    assert answers == ["hello\nworld"]
