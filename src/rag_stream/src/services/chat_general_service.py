from __future__ import annotations

import asyncio
import re
from typing import Any, Awaitable, Callable

from log_decorator import log
from DaiShanSQL import Server

from src.models.schemas import ChatRequest

server = Server()


@log(message="意图识别返回错误，跳过后处理", print_result=False)
def _skip_intent_error_result(result_dict: dict) -> None:
    _ = result_dict
    return None


@log(message="后处理兜底异常", print_result=False)
def _log_fallback_error_and_reraise(error: Exception) -> None:
    raise error


@log()
def _extract_questions_for_sql(text_input: str, result_items: list[dict]) -> list[str]:
    questions: list[str] = []
    for item in result_items:
        question_text = item.get("question", "")
        if question_text.startswith("Question: "):
            parts = question_text.split("\tAnswer: ", 1)
            if parts and parts[0].startswith("Question: "):
                extracted_question = parts[0][10:]
                questions.append(extracted_question.strip())

    if not questions:
        questions = [text_input]

    return questions


@log()
async def _post_process_type1(result_dict: dict) -> dict:
    result_items = result_dict.get("results", [])
    first_question = result_items[0].get("question", "") if result_items else ""
    kb_match = re.search(r"\[knowledgebase:(\w+)\]", first_question)

    if not kb_match:
        return {"type": 1, "data": {"kb_name": "园区知识库", "sql_result": "1"}}

    kb_name = kb_match.group(1)

    result = ""
    if kb_name == "园区知识库":
        result = "1"
    elif kb_name == "企业知识库":
        result = server.sqlFixed.sql_ChemicalCompanyInfo()
    elif kb_name == "安全信息知识库":
        result = server.sqlFixed.sql_SecuritySituation()

    return {"type": 1, "data": {"kb_name": kb_name, "sql_result": str(result)}}


@log()
async def _route_with_sql_result(
    request: ChatRequest,
    sql_result: Any,
    target_category: str,
    chat_with_category: Callable[[str, ChatRequest], Awaitable[Any]],
):
    if not target_category:
        return None

    sql_result_str = "" if sql_result is None else str(sql_result).strip()
    if not sql_result_str:
        return await chat_with_category(target_category, request)

    updated_request = ChatRequest(
        question=f"{request.question}\n\n{sql_result_str}",
        session_id=request.session_id,
        user_id=request.user_id,
        stream=request.stream,
    )

    return await chat_with_category(target_category, updated_request)


@log()
async def _post_process_and_route_type1(
    request: ChatRequest,
    result_dict: dict,
    chat_with_category: Callable[[str, ChatRequest], Awaitable[Any]],
):
    processed_result = await _post_process_type1(result_dict)
    data = processed_result.get("data", {})
    return await _route_with_sql_result(
        request=request,
        sql_result=data.get("sql_result", ""),
        target_category=data.get("kb_name", ""),
        chat_with_category=chat_with_category,
    )


@log()
async def _post_process_type2(text_input: str, result_dict: dict) -> dict:
    questions = _extract_questions_for_sql(text_input, result_dict.get("results", []))

    sql_result = await asyncio.to_thread(
        server.get_sql_result,
        query=text_input,
        history=[],
        questions=questions,
    )

    return {"type": 2, "data": {"sql_result": sql_result}}


@log()
async def _post_process_and_route_type2(
    request: ChatRequest,
    result_dict: dict,
    chat_with_category: Callable[[str, ChatRequest], Awaitable[Any]],
):
    processed_result = await _post_process_type2(request.question, result_dict)
    data = processed_result.get("data", {})
    return await _route_with_sql_result(
        request=request,
        sql_result=data.get("sql_result", ""),
        target_category="通用",
        chat_with_category=chat_with_category,
    )


@log()
async def handle_chat_general(
    request: ChatRequest,
    intent_service,
    chat_with_category: Callable[[str, ChatRequest], Awaitable[Any]],
):
    """通用问答业务逻辑（从路由层下沉）"""
    user_id = request.user_id or "anonymous"

    result_dict = await intent_service.process_query(request.question, user_id)

    result_type = result_dict.get("type")
    has_error = bool(result_dict.get("data", {}).get("error"))

    try:
        if has_error:
            _skip_intent_error_result(result_dict)
            return await chat_with_category("通用", request)
        elif result_type == 1:
            routed_result = await _post_process_and_route_type1(
                request=request,
                result_dict=result_dict,
                chat_with_category=chat_with_category,
            )
            if routed_result is not None:
                return routed_result
            return await chat_with_category("通用", request)
        else:
            routed_result = await _post_process_and_route_type2(
                request=request,
                result_dict=result_dict,
                chat_with_category=chat_with_category,
            )
            if routed_result is not None:
                return routed_result
            return await chat_with_category("通用", request)
    except ImportError as error:
        try:
            _log_fallback_error_and_reraise(error)
        except Exception:
            return await chat_with_category("通用", request)
    except Exception as error:
        try:
            _log_fallback_error_and_reraise(error)
        except Exception:
            return await chat_with_category("通用", request)
