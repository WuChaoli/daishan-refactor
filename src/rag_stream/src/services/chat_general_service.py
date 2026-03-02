from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
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
_PROMPT_MAPPING_DATA_DIR = Path(__file__).resolve().parent / "data"
_TYPE1_PROMPT_MAPPING_PATH = _PROMPT_MAPPING_DATA_DIR / "type1_question_mapping.json"
_TYPE2_PROMPT_MAPPING_PATH = _PROMPT_MAPPING_DATA_DIR / "type2_question_mapping.json"
_TYPE3_PROMPT_MAPPING_PATH = (
    _PROMPT_MAPPING_DATA_DIR / "fixed_question_prompt_mapping.json"
)
_prompt_mapping_cache: dict[str, dict[str, dict[str, Any]]] = {}


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
        question_text = str(item.get("question", "") or "")
        extracted_question = _extract_question_from_qa_text(question_text)
        if extracted_question:
            questions.append(extracted_question)
            continue

        normalized_question = question_text.strip()
        if normalized_question:
            questions.append(normalized_question)

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
def _extract_primary_question(result_items: list[dict]) -> str:
    if not result_items:
        return ""

    first_question = str(result_items[0].get("question", "") or "")
    extracted_question = _extract_question_from_qa_text(first_question)
    if extracted_question:
        return extracted_question
    return first_question.strip()


def _build_mapping_entry(raw_value: Any) -> dict[str, Any]:
    if isinstance(raw_value, dict):
        prompt_text = str(raw_value.get("prompt", "") or "").strip()
        meta = raw_value.get("meta", {})
        return {
            "prompt": prompt_text,
            "meta": meta if isinstance(meta, dict) else {},
        }
    return {"prompt": str(raw_value or "").strip(), "meta": {}}


@trace
def _load_prompt_mapping(mapping_type: str, mapping_path: Path) -> dict[str, dict[str, Any]]:
    cached_mapping = _prompt_mapping_cache.get(mapping_type)
    if cached_mapping is not None:
        return cached_mapping

    try:
        mapping_payload = json.loads(mapping_path.read_text(encoding="utf-8"))
        if not isinstance(mapping_payload, dict):
            raise ValueError(f"{mapping_type} prompt mapping root must be object")

        normalized_mapping: dict[str, dict[str, Any]] = {}
        for key, value in mapping_payload.items():
            normalized_key = str(key).strip()
            if not normalized_key:
                continue

            entry = _build_mapping_entry(value)
            if not entry.get("prompt", ""):
                continue
            normalized_mapping[normalized_key] = entry

        _prompt_mapping_cache[mapping_type] = normalized_mapping
        marker(
            f"{mapping_type}.prompt_mapping_loaded",
            {
                "entries": len(normalized_mapping),
                "file": mapping_path.name,
            },
        )
    except FileNotFoundError:
        marker(
            f"{mapping_type}.prompt_mapping_missing",
            {"file": str(mapping_path)},
            level="WARNING",
        )
        _prompt_mapping_cache[mapping_type] = {}
    except Exception as error:
        marker(
            f"{mapping_type}.prompt_mapping_load_failed",
            {"error": str(error), "file": mapping_path.name},
            level="WARNING",
        )
        _prompt_mapping_cache[mapping_type] = {}

    return _prompt_mapping_cache[mapping_type]


@trace
def _find_mapping_prompt_by_question(
    mapping_type: str,
    mapping_path: Path,
    question: str,
) -> str:
    normalized_question = str(question or "").strip()
    prompt_text = ""
    if normalized_question:
        matched_prompt = _load_prompt_mapping(mapping_type, mapping_path).get(
            normalized_question, {}
        )
        prompt_text = str(matched_prompt.get("prompt", "") or "").strip()

    marker(
        f"{mapping_type}.prompt_mapping_lookup",
        {"matched": bool(prompt_text), "question_len": len(normalized_question)},
    )
    return prompt_text


def _clear_prompt_mapping_cache() -> None:
    _prompt_mapping_cache.clear()


@trace
def _find_type1_mapping_by_question(question: str) -> str:
    return _find_mapping_prompt_by_question(
        mapping_type="type1",
        mapping_path=_TYPE1_PROMPT_MAPPING_PATH,
        question=question,
    )


@trace
def _find_type2_mapping_by_question(question: str) -> str:
    return _find_mapping_prompt_by_question(
        mapping_type="type2",
        mapping_path=_TYPE2_PROMPT_MAPPING_PATH,
        question=question,
    )


@trace
def _find_type3_prompt_by_question(question: str) -> str:
    return _find_mapping_prompt_by_question(
        mapping_type="type3",
        mapping_path=_TYPE3_PROMPT_MAPPING_PATH,
        question=question,
    )


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
    prefix_text: str = "",
):
    if not target_category:
        return None

    sql_result_str = "" if sql_result is None else str(sql_result).strip()
    if not sql_result_str:
        return await chat_with_category(target_category, request)

    prefix_value = str(prefix_text or "").strip()
    merged_question = f"{request.question}\n\n{sql_result_str}"
    if prefix_value:
        merged_question = f"{prefix_value}\n\n{merged_question}"

    updated_request = ChatRequest(
        question=merged_question,
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
    primary_question = _extract_primary_question(result_dict.get("results", []))
    mapped_prompt = _find_type1_mapping_by_question(primary_question)
    if not mapped_prompt:
        marker(
            "type1.prompt_unavailable_fallback_general",
            {"question_len": len(primary_question)},
            level="WARNING",
        )
        return await chat_with_category("通用", request)

    mapped_request = ChatRequest(
        question=f"{mapped_prompt}\n\n{request.question}",
        session_id=request.session_id,
        user_id=request.user_id,
        stream=request.stream,
    )

    processed_result = await _post_process_type1(result_dict)
    data = processed_result.get("data", {})
    return await _route_with_sql_result(
        request=mapped_request,
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
    primary_question = _extract_primary_question(result_dict.get("results", []))
    mapped_prompt = _find_type2_mapping_by_question(primary_question)
    if not mapped_prompt:
        marker(
            "type2.prompt_unavailable_fallback_general",
            {"question_len": len(primary_question)},
            level="WARNING",
        )
        return await chat_with_category("通用", request)

    processed_result = await _post_process_type2(request.question, result_dict)
    data = processed_result.get("data", {})
    return await _route_with_sql_result(
        request=request,
        sql_result=data.get("sql_result", ""),
        target_category="通用",
        chat_with_category=chat_with_category,
        prefix_text=mapped_prompt,
    )


async def _post_process_and_route_type3(
    request: ChatRequest,
    result_dict: dict,
    chat_with_category: Callable[[str, ChatRequest], Awaitable[Any]],
):
    result_items = result_dict.get("results", [])
    first_question = result_items[0].get("question", "") if result_items else ""
    return_question = _extract_question_from_qa_text(first_question)
    if not return_question:
        return None

    mapped_prompt = _find_type3_prompt_by_question(return_question)
    fallback_prompt = str(result_dict.get("answer", "") or "").strip()
    answer_text = mapped_prompt or fallback_prompt
    if not answer_text:
        marker(
            "type3.prompt_unavailable",
            {"question_len": len(return_question)},
            level="WARNING",
        )
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
