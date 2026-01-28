from __future__ import annotations

import json
import logging
import re
import time
import os
from typing import Optional

import aiohttp

from src.config.settings import settings

logger = logging.getLogger(__name__)
_SUPPRESS_INTERNAL_LOGS = os.getenv("DIFY_SUPPRESS_INTERNAL_LOGS", "").lower() in {"1", "true", "yes", "on"}
if _SUPPRESS_INTERNAL_LOGS:
    logger.setLevel(logging.ERROR)


def should_use_dify(request_question: str) -> bool:
    q = request_question.strip()
    patterns = [
        r"介绍.*园区",
        r"园区.*介绍",
        r"介绍一下园区",
        r"园区.*情况",
        r"园区.*信息",
        r"介绍.*企业",
        r"介绍.*公司",
        r"企业.*介绍",
        r"介绍.*园区.*安全",
        r"园区.*安全.*状况",
        r"园区.*是否安全",
        r"园区安全.*介绍",
        r".*安全状况",
    ]
    return any(re.search(pat, q) for pat in patterns)


async def stream_dify_chatflow_response(
    query: str,
    session_id: Optional[str],
    user_id: Optional[str] = None,
    dify_conversation_id: Optional[str] = None,
):
    url = settings.DIFY_API_URL
    api_key = settings.DIFY_API_KEY

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "inputs": {},
        "query": query,
        "response_mode": "streaming",
        "conversation_id": dify_conversation_id or "",
        "user": user_id or "anonymous",
    }

    old_answer = ""
    word_id = 0
    start_time = time.time()
    first_output_sent = False
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Dify Chatflow 返回错误: {response.status} - {error_text}")
                    yield f"data: {json.dumps({'code': 1, 'message': f'Dify 服务错误: {error_text}', 'data': None}, ensure_ascii=False)}\n\n"
                    return

                buffer = b""
                async for chunk in response.content:
                    buffer += chunk
                    while b"\n" in buffer:
                        raw_line, buffer = buffer.split(b"\n", 1)
                        line_text = raw_line.decode("utf-8", errors="ignore").strip()

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

                        if not line_text:
                            continue

                        if line_text.startswith("data:"):
                            data_str = line_text[5:].strip()
                            if data_str == "[DONE]":
                                break

                            try:
                                json_data = json.loads(data_str)
                            except json.JSONDecodeError:
                                continue

                            answer = json_data.get("answer", "")
                            if not answer and "message" in json_data:
                                answer = json_data.get("message", {}).get("content", "")

                            if answer:
                                if not old_answer:
                                    incremental_answer = answer
                                    old_answer = answer
                                elif answer.startswith(old_answer):
                                    incremental_answer = answer[len(old_answer) :]
                                    old_answer = answer
                                elif answer in old_answer or old_answer.startswith(answer) or len(answer) <= len(old_answer):
                                    # 子串/回退/变短：忽略，避免 end=0 重复 chunk
                                    continue
                                else:
                                    # 非追加更新（可能是插入/改写）：忽略以避免重复输出
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
        logger.exception(f"Dify Chatflow 流式调用异常: {e}")
        error_data = {"code": 1, "message": f"流式处理失败: {str(e)}", "data": None}
        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
