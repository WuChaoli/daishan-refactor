from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Optional

import aiohttp
from fastapi import HTTPException
from src.utils.log_manager_import import trace, marker

from src.config.settings import settings
from src.utils.session_manager import session_manager

@trace
async def get_rag_client():
    """获取RAG客户端会话"""
    timeout = aiohttp.ClientTimeout(total=settings.ragflow.timeout)
    return aiohttp.ClientSession(timeout=timeout)


@trace
async def create_rag_session(
    chat_id: str, session_name: str, user_id: Optional[str] = None
) -> str:
    """在RAG服务中创建会话"""
    marker("创建RAG会话开始", {"chat_id": chat_id, "session_name": session_name, "has_user_id": bool(user_id)})
    async with aiohttp.ClientSession() as session:
        url = f"{settings.ragflow.base_url}/chats/{chat_id}/sessions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.ragflow.api_key}",
        }
        data = {"name": session_name}
        if user_id:
            data["user_id"] = user_id

        try:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("code") == 0:
                        marker("创建RAG会话成功", {"rag_session_id": result['data']['id']})
                        return result["data"]["id"]
                    raise HTTPException(
                        status_code=400,
                        detail=f"RAG创建会话失败: {result.get('message')}",
                    )
                raise HTTPException(status_code=response.status, detail="RAG服务响应错误")
        except Exception as e:
            marker("创建RAG会话失败", {"error": str(e)}, level="ERROR")
            raise HTTPException(status_code=500, detail=f"创建RAG会话失败: {str(e)}")


@trace
async def get_or_create_session(
    chat_id: str, category: str, user_id: Optional[str] = None
) -> str:
    """获取或创建用户会话"""
    session_manager.cleanup_all_expired_sessions()

    if user_id:
        existing_session_id = session_manager.get_user_session(user_id, category)
        if existing_session_id:
            marker("使用现有会话", {"session_id": existing_session_id, "user_id": user_id, "category": category})
            marker("命中现有会话", {"session_id": existing_session_id, "user_id": user_id, "category": category})
            return existing_session_id

    session_name = f"{category}_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    rag_session_id = await create_rag_session(chat_id, session_name, user_id)

    local_session_id = session_manager.create_session(chat_id, session_name, user_id, category)

    session_manager.sessions[local_session_id]["rag_session_id"] = rag_session_id

    marker("创建新会话", {"local_session_id": local_session_id, "rag_session_id": rag_session_id, "user_id": user_id, "category": category})
    marker("新会话创建完成", {"local_session_id": local_session_id, "rag_session_id": rag_session_id})
    return local_session_id


@trace
async def stream_chat_response(
    chat_id: str, question: str, session_id: str, user_id: Optional[str] = None
):
    """流式聊天响应"""
    rag_session_id = session_manager.sessions.get(session_id, {}).get("rag_session_id", session_id)
    marker("RAG流式响应开始", {"chat_id": chat_id, "session_id": session_id, "has_user_id": bool(user_id)})

    url = f"{settings.ragflow.base_url}/chats/{chat_id}/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.ragflow.api_key}",
    }
    data = {"question": question, "stream": True, "session_id": rag_session_id}
    if user_id:
        data["user_id"] = user_id
    start_time = time.time()
    first_output_sent = False
    end_sent = False
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    marker("RAG流式响应状态异常", {"status": response.status}, level="ERROR")
                    yield f"data: {json.dumps({'code': 1, 'message': f'RAG服务错误: {error_text}', 'data': None})}\n\n"
                    return

                session_manager.update_session_activity(session_id)

                old_answer = ""
                word_id = 0
                buffer = b""
                async for chunk in response.content:
                    buffer += chunk
                    while b"\n" in buffer:
                        raw_line, buffer = buffer.split(b"\n", 1)
                        line_text = raw_line.decode("utf-8", errors="ignore").strip()

                        if not first_output_sent and (time.time() - start_time > 15):
                            timeout_data = {
                                "code": 1,
                                "message": "当前网络异常，请稍后再试。",
                                "data": {
                                    "sessionId": session_id,
                                    "answer": "当前网络异常，请稍后再试。",
                                    "flag": 1,
                                    "wordId": word_id,
                                    "end": 0,
                                },
                            }
                            yield f"data: {json.dumps(timeout_data, ensure_ascii=False)}\n\n"
                            timeout_data1 = {
                                "code": 1,
                                "data": {
                                    "sessionId": session_id,
                                    "answer": "",
                                    "flag": 0,
                                    "wordId": word_id + 1,
                                    "end": 1,
                                },
                            }
                            yield f"data: {json.dumps(timeout_data1, ensure_ascii=False)}\n\n"
                            return

                        if not line_text:
                            continue

                        if line_text.startswith("data:"):
                            data_content = line_text.replace("data:", "", 1).strip()

                            try:
                                json_data = json.loads(data_content)
                                if json_data.get("code") == 0:
                                    data_field = json_data.get("data")
                                    if data_field and isinstance(data_field, dict):
                                        answer = data_field.get("answer", "")
                                        if answer:
                                            # 仅接受“前缀追加”的增量。
                                            # RAGFlow 有时会在最后一条把历史文本做“中间插入/改写”（如插入引用标记 ##x$$ 和 reference），
                                            # 这会导致把整段答案再输出一遍（前端看起来像复制了一遍）。这种非前缀更新直接忽略。
                                            if answer == old_answer:
                                                continue

                                            if not old_answer:
                                                incremental_answer = answer
                                                old_answer = answer
                                            elif answer.startswith(old_answer):
                                                incremental_answer = answer[len(old_answer) :]
                                                old_answer = answer
                                            else:
                                                continue

                                            if not first_output_sent:
                                                first_output_sent = True

                                            if not first_output_sent and time.time() - start_time > 15:
                                                timeout_data = {
                                                    "code": 1,
                                                    "message": "当前网络异常，请稍后再试。",
                                                    "data": {
                                                        "sessionId": session_id,
                                                        "answer": "当前网络异常，请稍后再试。",
                                                        "flag": 1,
                                                        "wordId": word_id,
                                                        "end": 0,
                                                    },
                                                }
                                                yield f"data: {json.dumps(timeout_data, ensure_ascii=False)}\n\n"

                                                timeout_data1 = {
                                                    "code": 1,
                                                    "data": {
                                                        "sessionId": session_id,
                                                        "answer": "",
                                                        "flag": 0,
                                                        "wordId": word_id + 1,
                                                        "end": 1,
                                                    },
                                                }
                                                yield f"data: {json.dumps(timeout_data1, ensure_ascii=False)}\n\n"
                                                return

                                            stream_data = {
                                                "code": 0,
                                                "data": {
                                                    "sessionId": session_id,
                                                    "answer": incremental_answer,
                                                    "flag": 1,
                                                    "wordId": word_id,
                                                    "end": 0,
                                                },
                                            }
                                            word_id += 1
                                            yield f"data: {json.dumps(stream_data, ensure_ascii=False)}\n\n"

                                        elif data_field is True:
                                            end_data = {
                                                "code": 0,
                                                "data": {
                                                    "sessionId": session_id,
                                                    "answer": "",
                                                    "flag": 0,
                                                    "wordId": word_id,
                                                    "end": 1,
                                                },
                                            }
                                            yield f"data: {json.dumps(end_data, ensure_ascii=False)}\n\n"
                                            end_sent = True
                                            return

                                        elif data_field == "true" or data_field == "True":
                                            end_data = {
                                                "code": 0,
                                                "data": {
                                                    "sessionId": session_id,
                                                    "answer": "",
                                                    "flag": 0,
                                                    "wordId": word_id,
                                                    "end": 1,
                                                },
                                            }
                                            yield f"data: {json.dumps(end_data, ensure_ascii=False)}\n\n"
                                            end_sent = True
                                            return

                            except json.JSONDecodeError:
                                continue

                if not end_sent:
                    end_data = {
                        "code": 0,
                        "data": {
                            "sessionId": session_id,
                            "answer": "",
                            "flag": 0,
                            "wordId": word_id,
                            "end": 1,
                        },
                    }
                    yield f"data: {json.dumps(end_data, ensure_ascii=False)}\n\n"

                marker("RAG流式响应结束", {"session_id": session_id, "chunks": word_id})

    except Exception as e:
        marker("流式响应处理失败", {"error": str(e)}, level="ERROR")
        marker("RAG流式响应异常", {"error": str(e)}, level="ERROR")
        error_data = {"code": 1, "message": f"流式响应处理失败: {str(e)}", "data": None}
        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
