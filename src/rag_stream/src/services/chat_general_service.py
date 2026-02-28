from __future__ import annotations

import asyncio
import re
from typing import Any, Awaitable, Callable

from rag_stream.config.settings import settings
from rag_stream.utils.log_manager_import import entry_trace, marker, trace
from rag_stream.utils.daishan_sql_logging import format_daishan_log_text
from rag_stream.utils.query_chat import rewrite_query

try:
    from DaiShanSQL.DaiShanSQL.api_server import Server
except ModuleNotFoundError:
    from DaiShanSQL import Server

from rag_stream.models.schemas import ChatRequest

_server: Server | None = None


def _get_server() -> Server:
    global _server
    if _server is None:
        _server = Server()
    return _server


def _skip_intent_error_result(result_dict: dict) -> None:
    _ = result_dict
    return None


def _log_fallback_error_and_reraise(error: Exception) -> None:
    raise error


@trace
async def replace_economic_zone(query: str) -> str:
    """
    使用 AI 对 query 进行企业名称清理。

    始终调用模型进行问题删除，不再依赖关键词触发。
    失败时返回原 query，不再执行正则替换。
    """
    if not isinstance(query, str) or not query:
        marker(
            "query_normalized_skip_invalid",
            {"input_type": type(query).__name__ if query is not None else "None"},
            level="WARNING",
        )
        return query

    if not settings.query_chat.enabled:
        marker("query_normalized_disabled", {"query_len": len(query)})
        return query

    if (
        not (settings.query_chat.api_key or "").strip()
        or not (settings.query_chat.base_url or "").strip()
    ):
        marker("query_normalized_misconfigured", {"query_len": len(query)})
        return query

    marker("query_normalized_start", {"query_len": len(query)})
    try:
        rewritten = await rewrite_query(query, settings.query_chat)
    except Exception as error:
        marker("query_normalized_failed", {"error": str(error)}, level="WARNING")
        return query

    rewritten_text = str(rewritten).strip() if rewritten is not None else ""
    if not rewritten_text:
        marker("query_normalized_empty", {}, level="WARNING")
        return query

    marker("query_normalized", {"normalized": rewritten_text != query})
    return rewritten_text


@trace
def _extract_questions_for_sql(text_input: str, result_items: list[dict]) -> list[str]:
    marker(
        "extract_questions.start",
        {"text_len": len(text_input or ""), "candidates": len(result_items or [])},
    )
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
        marker("extract_questions.fallback_to_input")

    return questions


@trace
def _extract_question_from_qa_text(question_text: str) -> str:
    marker("extract_question_from_qa.start", {"text_len": len(question_text or "")})
    if not isinstance(question_text, str):
        return ""

    if question_text.startswith("Question: "):
        parts = question_text.split("\tAnswer: ", 1)
        if parts and parts[0].startswith("Question: "):
            extracted = parts[0][10:].strip()
            return extracted

    return ""


@trace
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
        marker(
            "DaiShanSQL入参",
            {"入参": format_daishan_log_text("sql_ChemicalCompanyInfo()")},
        )
        try:
            result = _get_server().sqlFixed.sql_ChemicalCompanyInfo()
            marker("DaiShanSQL出参", {"出参": format_daishan_log_text(result)})
        except Exception as error:
            marker(
                "DaiShanSQL出参",
                {"出参": format_daishan_log_text(f"ERROR: {error}")},
                level="ERROR",
            )
            raise
    elif kb_name == "安全信息知识库":
        marker(
            "DaiShanSQL入参",
            {"入参": format_daishan_log_text("sql_SecuritySituation()")},
        )
        try:
            result = _get_server().sqlFixed.sql_SecuritySituation()
            marker("DaiShanSQL出参", {"出参": format_daishan_log_text(result)})
        except Exception as error:
            marker(
                "DaiShanSQL出参",
                {"出参": format_daishan_log_text(f"ERROR: {error}")},
                level="ERROR",
            )
            raise

    marker(
        "type1.sql_result_ready",
        {"kb_name": kb_name, "result_len": len(str(result or ""))},
    )
    return {"type": 1, "data": {"kb_name": kb_name, "sql_result": str(result)}}


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


async def _post_process_type2(text_input: str, result_dict: dict) -> dict:
    questions = _extract_questions_for_sql(text_input, result_dict.get("results", []))

    marker(
        "DaiShanSQL入参",
        {
            "入参": format_daishan_log_text(
                {
                    "query": text_input,
                    "history": [],
                    "questions": questions,
                }
            )
        },
    )
    try:
        sql_result = await asyncio.to_thread(
            _get_server().get_sql_result,
            query=text_input,
            history=[],
            questions=questions,
        )
        marker("DaiShanSQL出参", {"出参": format_daishan_log_text(sql_result)})
    except Exception as error:
        marker(
            "DaiShanSQL出参",
            {"出参": format_daishan_log_text(f"ERROR: {error}")},
            level="ERROR",
        )
        raise

    return {"type": 2, "data": {"sql_result": sql_result}}


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


async def _post_process_and_route_type3(
    request: ChatRequest,
    result_dict: dict,
    chat_with_category: Callable[[str, ChatRequest], Awaitable[Any]],
):
    answer_text = str(result_dict.get("answer", "") or "").strip()
    if not answer_text:
        return None

    result_items = result_dict.get("results", [])
    first_question = result_items[0].get("question", "") if result_items else ""
    return_question = _extract_question_from_qa_text(first_question)
    if not return_question:
        return None

    try:
        marker(
            "DaiShanSQL入参",
            {
                "入参": format_daishan_log_text(
                    {
                        "query": request.question,
                        "return_question": return_question,
                    }
                )
            },
        )
        judge_result = await asyncio.to_thread(
            _get_server().judgeQuery,
            request.question,
            return_question,
        )
        marker("DaiShanSQL出参", {"出参": format_daishan_log_text(judge_result)})
    except Exception as error:
        marker(
            "DaiShanSQL出参",
            {"出参": format_daishan_log_text(f"ERROR: {error}")},
            level="ERROR",
        )
        return None

    judge_result_str = "" if judge_result is None else str(judge_result).strip()
    if not judge_result_str:
        return None

    updated_request = ChatRequest(
        question=f"{answer_text}\n\n{judge_result_str}\n\n{request.question}",
        session_id=request.session_id,
        user_id=request.user_id,
        stream=request.stream,
    )
    return await chat_with_category("通用", updated_request)


@entry_trace("chat-general")
async def handle_chat_general(
    request: ChatRequest,
    intent_service,
    chat_with_category: Callable[[str, ChatRequest], Awaitable[Any]],
):
    """通用问答业务逻辑（从路由层下沉）"""

    user_id = request.user_id or "anonymous"
    original_question = request.question

    if isinstance(request.question, str):
        request.question = await replace_economic_zone(request.question)

    try:
        result_dict = await intent_service.process_query(request.question, user_id)
    finally:
        request.question = original_question

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
        elif result_type == 3:
            routed_result = await _post_process_and_route_type3(
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
