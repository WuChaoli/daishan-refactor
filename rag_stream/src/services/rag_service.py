from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from typing import Optional

import aiohttp
from fastapi import HTTPException

from src.config.settings import settings
from src.utils.session_manager import session_manager

logger = logging.getLogger(__name__)


async def get_rag_client():
    """获取RAG客户端会话"""
    timeout = aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT)
    return aiohttp.ClientSession(timeout=timeout)


async def create_rag_session(
    chat_id: str, session_name: str, user_id: Optional[str] = None
) -> str:
    """在RAG服务中创建会话"""
    async with aiohttp.ClientSession() as session:
        url = f"{settings.RAG_BASE_URL}/api/v1/chats/{chat_id}/sessions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.RAG_API_KEY}",
        }
        data = {"name": session_name}
        if user_id:
            data["user_id"] = user_id

        try:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("code") == 0:
                        return result["data"]["id"]
                    raise HTTPException(
                        status_code=400,
                        detail=f"RAG创建会话失败: {result.get('message')}",
                    )
                raise HTTPException(status_code=response.status, detail="RAG服务响应错误")
        except Exception as e:
            logger.error(f"创建RAG会话失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"创建RAG会话失败: {str(e)}")


async def get_or_create_session(
    chat_id: str, category: str, user_id: Optional[str] = None
) -> str:
    """获取或创建用户会话"""
    session_manager.cleanup_all_expired_sessions()

    if user_id:
        existing_session_id = session_manager.get_user_session(user_id, category)
        if existing_session_id:
            logger.info(
                f"使用现有会话: {existing_session_id}, 用户: {user_id}, 类别: {category}"
            )
            return existing_session_id

    session_name = f"{category}_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    rag_session_id = await create_rag_session(chat_id, session_name, user_id)

    local_session_id = session_manager.create_session(chat_id, session_name, user_id, category)

    session_manager.sessions[local_session_id]["rag_session_id"] = rag_session_id

    logger.info(
        f"创建新会话: {local_session_id}, RAG会话: {rag_session_id}, 用户: {user_id}, 类别: {category}"
    )
    return local_session_id


async def stream_chat_response(
    chat_id: str, question: str, session_id: str, user_id: Optional[str] = None
):
    """流式聊天响应"""
    rag_session_id = session_manager.sessions.get(session_id, {}).get("rag_session_id", session_id)

    url = f"{settings.RAG_BASE_URL}/api/v1/chats/{chat_id}/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.RAG_API_KEY}",
    }
    data = {"question": question, "stream": True, "session_id": rag_session_id}
    if user_id:
        data["user_id"] = user_id
    start_time = time.time()
    first_output_sent = False
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
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
                                            if old_answer and answer.startswith(old_answer):
                                                incremental_answer = answer[len(old_answer) :]
                                            else:
                                                incremental_answer = answer

                                            old_answer = answer

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
                                            break

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
                                            break

                            except json.JSONDecodeError:
                                continue

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

    except Exception as e:
        logger.error(f"流式响应处理失败: {str(e)}")
        error_data = {"code": 1, "message": f"流式响应处理失败: {str(e)}", "data": None}
        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
