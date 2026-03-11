from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any, Awaitable, Callable

from rag_stream.config.settings import settings
from rag_stream.services.fixed_question_flow_service import (
    query_fixed_question_candidates,
    replace_daishan_zone_alias,
    select_top_candidates,
)
from rag_stream.utils.log_manager_import import marker
from rag_stream.utils.query_chat import (
    rerank_fixed_question_candidates,
    rewrite_query,
)

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
LOW_CONFIDENCE_REPLY = "对不起，该问题超出系统回答范围，请重新提问"


def _build_ragflow_result_log(
    original_question: str,
    q1: str,
    q2: str,
    all_candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    top_candidates: list[dict[str, Any]] = []
    for item in all_candidates[:3]:
        top_candidates.append(
            {
                "question": str(item.get("question", "") or ""),
                "similarity": float(item.get("similarity", 0.0) or 0.0),
            }
        )
    return {
        "query_original": str(original_question or ""),
        "query_q1": str(q1 or ""),
        "query_q2": str(q2 or ""),
        "table_name": str(settings.intent.fixed_question_table_name),
        "candidate_count": len(all_candidates),
        "top_candidates": top_candidates,
    }


def _build_intent_decision_log(
    candidates: list[dict[str, Any]],
    decision: str,
    selected_question: str = "",
    selected_similarity: float = 0.0,
    reason: str = "",
) -> dict[str, Any]:
    best_candidate = candidates[0] if candidates else {}
    return {
        "decision": decision,
        "reason": reason,
        "selected_question": str(selected_question or ""),
        "selected_similarity": float(selected_similarity or 0.0),
        "best_question": str(best_candidate.get("question", "") or ""),
        "best_similarity": float(best_candidate.get("similarity", 0.0)) if best_candidate else 0.0,
        "similarity_threshold": float(settings.intent.fixed_question_similarity_threshold),
        "direct_threshold": float(settings.intent.fixed_question_direct_threshold),
    }


def _log_daishansql_call(
    called: bool,
    method: str = "",
    request_payload: Any = None,
    sql_text: Any = "",
    result: Any = None,
    reason: str = "",
    sql_source: str = "unavailable",
    error: str = "",
    level: str = "INFO",
) -> None:
    marker(
        "chat_general.daishansql",
        {
            "called": called,
            "method": method,
            "request": request_payload,
            "sql_source": sql_source,
            "sql_text": sql_text,
            "result": result,
            "reason": reason,
            "error": error,
        },
        level=level,
    )


def _extract_sql_texts_from_agent_result(sql_result: Any) -> list[str]:
    sql_texts: list[str] = []
    if not isinstance(sql_result, list):
        return sql_texts
    for item in sql_result:
        if not isinstance(item, dict):
            continue
        sql_value = item.get("sql语句", "")
        if isinstance(sql_value, set):
            sql_texts.extend(str(part) for part in sql_value if str(part).strip())
            continue
        if isinstance(sql_value, (list, tuple)):
            sql_texts.extend(str(part) for part in sql_value if str(part).strip())
            continue
        if str(sql_value).strip():
            sql_texts.append(str(sql_value).strip())
    return sql_texts


def _consume_execution_logs(executor: Any) -> list[dict[str, Any]]:
    consume = getattr(executor, "consume_last_execution_log", None)
    if not callable(consume):
        return []
    try:
        logs = consume()
    except Exception:
        return []
    return logs if isinstance(logs, list) else []


def _extract_sql_texts_from_execution_logs(logs: list[dict[str, Any]]) -> list[str]:
    sql_texts: list[str] = []
    for item in logs:
        if not isinstance(item, dict):
            continue
        sql_text = str(item.get("sql_text", "") or "").strip()
        if sql_text:
            sql_texts.append(sql_text)
    return sql_texts


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


async def replace_economic_zone(query: str) -> str:
    """
    使用 AI 对 q2 生成占位化后的 q1。

    始终调用模型进行占位替换，不再依赖关键词触发。
    失败时返回原 query。
    """
    if not isinstance(query, str) or not query:
        return query

    if not settings.query_chat.enabled:
        return query

    if (
        not (settings.query_chat.api_key or "").strip()
        or not (settings.query_chat.base_url or "").strip()
    ):
        return query

    try:
        rewritten = await rewrite_query(query, settings.query_chat)
    except Exception:
        return query

    rewritten_text = str(rewritten).strip() if rewritten is not None else ""
    if not rewritten_text:
        return query

    return rewritten_text


async def _build_query_variants(query: str) -> tuple[str, str]:
    if not isinstance(query, str):
        return query, query

    q2 = replace_daishan_zone_alias(query)
    q1 = await replace_economic_zone(q2)
    return q1, q2


def _build_chat_request_with_question(request: ChatRequest, question: str) -> ChatRequest:
    return ChatRequest(
        question=question,
        session_id=request.session_id,
        user_id=request.user_id,
        stream=request.stream,
    )


def _build_fixed_question_candidate_log_items(
    candidates: list[dict[str, Any]],
    limit: int = 5,
) -> list[dict[str, Any]]:
    log_items: list[dict[str, Any]] = []
    for index, item in enumerate(candidates[: max(int(limit), 0)], start=1):
        log_items.append(
            {
                "rank": index,
                "question": str(item.get("question", "") or ""),
                "raw_question": str(item.get("raw_question", "") or ""),
                "similarity": float(item.get("similarity", 0.0)),
            }
        )
    return log_items


def _build_fixed_question_ragflow_result_log(
    original_question: str,
    rewritten_question: str,
    alias_replaced_question: str,
    all_candidates: list[dict[str, Any]],
    top_candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    similarity_threshold = float(settings.intent.fixed_question_similarity_threshold)
    direct_threshold = float(settings.intent.fixed_question_direct_threshold)
    return {
        "query_original": str(original_question or ""),
        "query_rewritten": str(rewritten_question or ""),
        "query_alias_replaced": str(alias_replaced_question or ""),
        "similarity_threshold": similarity_threshold,
        "direct_threshold": direct_threshold,
        "ragflow_candidate_count": len(all_candidates),
        "selected_pool_count": len(top_candidates),
        "ragflow_candidates": _build_fixed_question_candidate_log_items(all_candidates),
        "selected_pool": _build_fixed_question_candidate_log_items(top_candidates),
    }


def _build_fixed_question_decision_log(
    candidates: list[dict[str, Any]],
    decision: str,
    selected_question: str = "",
    rerank_selected_question: str = "",
    reason: str = "",
) -> dict[str, Any]:
    similarity_threshold = float(settings.intent.fixed_question_similarity_threshold)
    direct_threshold = float(settings.intent.fixed_question_direct_threshold)
    best_candidate = candidates[0] if candidates else {}
    return {
        "decision": decision,
        "reason": reason,
        "selected_question": str(selected_question or ""),
        "rerank_selected_question": str(rerank_selected_question or ""),
        "candidate_count": len(candidates),
        "best_question": str(best_candidate.get("question", "") or ""),
        "best_similarity": float(best_candidate.get("similarity", 0.0)) if best_candidate else 0.0,
        "similarity_threshold": similarity_threshold,
        "direct_threshold": direct_threshold,
        "candidates": _build_fixed_question_candidate_log_items(candidates),
    }


def _pick_candidate_by_question(
    candidates: list[dict[str, Any]],
    selected_question: str,
) -> dict[str, Any]:
    normalized_selected = str(selected_question or "").strip()
    if not normalized_selected:
        return candidates[0]

    for item in candidates:
        if str(item.get("question", "")).strip() == normalized_selected:
            return item

    return candidates[0]


async def _pick_fixed_question_candidate(
    original_question: str,
    candidates: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if not candidates:
        return None, _build_intent_decision_log(
            candidates=candidates,
            decision="fallback",
            reason="no_candidates",
        )

    similarity_threshold = float(settings.intent.fixed_question_similarity_threshold)
    direct_threshold = float(settings.intent.fixed_question_direct_threshold)

    best_candidate = candidates[0]
    best_similarity = float(best_candidate.get("similarity", 0.0))
    selected_question = str(best_candidate.get("question", "") or "")

    if best_similarity >= direct_threshold:
        return best_candidate, _build_intent_decision_log(
            candidates=candidates,
            decision="direct_hit",
            selected_question=selected_question,
            selected_similarity=best_similarity,
        )

    if best_similarity > similarity_threshold and len(candidates) == 1:
        return best_candidate, _build_intent_decision_log(
            candidates=candidates,
            decision="single_candidate_direct_hit",
            selected_question=selected_question,
            selected_similarity=best_similarity,
        )

    if similarity_threshold <= best_similarity < direct_threshold and len(candidates) > 1:
        rerank_question = await rerank_fixed_question_candidates(
            original_question,
            [str(item.get("question", "") or "") for item in candidates],
            settings.query_chat,
        )
        selected_candidate = _pick_candidate_by_question(candidates, rerank_question)
        return selected_candidate, _build_intent_decision_log(
            candidates=candidates,
            decision="rerank_select" if rerank_question else "rerank_fallback_first",
            selected_question=str(selected_candidate.get("question", "") or ""),
            selected_similarity=float(selected_candidate.get("similarity", 0.0) or 0.0),
            reason=str(rerank_question or ""),
        )

    fallback_reason = "single_candidate_at_similarity_threshold"
    if best_similarity < similarity_threshold:
        fallback_reason = "below_similarity_threshold"
    elif len(candidates) > 1:
        fallback_reason = "no_fixed_question_selected"

    return None, _build_intent_decision_log(
        candidates=candidates,
        decision="fallback",
        reason=fallback_reason,
    )


def _build_fixed_question_fallback_log(
    all_candidates: list[dict[str, Any]],
    top_candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    similarity_threshold = float(settings.intent.fixed_question_similarity_threshold)
    direct_threshold = float(settings.intent.fixed_question_direct_threshold)
    best_similarity = 0.0
    if all_candidates:
        best_similarity = float(all_candidates[0].get("similarity", 0.0))

    if not all_candidates:
        reason = "no_candidates"
    elif not top_candidates:
        reason = "below_similarity_threshold"
    elif len(top_candidates) == 1 and best_similarity == similarity_threshold:
        reason = "single_candidate_at_similarity_threshold"
    else:
        reason = "no_fixed_question_selected"

    return {
        "reason": reason,
        "best_similarity": best_similarity,
        "raw_candidate_count": len(all_candidates),
        "top_candidate_count": len(top_candidates),
        "similarity_threshold": similarity_threshold,
        "direct_threshold": direct_threshold,
        "top_questions": [
            str(item.get("question", "") or "") for item in top_candidates[:3]
        ],
    }


async def _route_low_confidence_to_general(
    request: ChatRequest,
    chat_with_category: Callable[[str, ChatRequest], Awaitable[Any]],
):
    low_confidence_request = _build_chat_request_with_question(request, LOW_CONFIDENCE_REPLY)
    return await chat_with_category("通用", low_confidence_request)


async def _route_selected_fixed_question(
    request: ChatRequest,
    q2: str,
    selected_question: str,
    chat_with_category: Callable[[str, ChatRequest], Awaitable[Any]],
):
    mapped_prompt = _find_type3_prompt_by_question(selected_question)
    if not mapped_prompt:
        _log_daishansql_call(
            called=False,
            method="judgeQuery",
            request_payload={"query_q2": q2, "fixed_question": selected_question},
            reason="prompt_unavailable",
        )
        return await chat_with_category("通用", request)

    server = _get_server()
    _consume_execution_logs(getattr(server, "sqlPlus", None))
    try:
        sql_result = await asyncio.to_thread(
            server.judgeQuery,
            q2,
            selected_question,
        )
        execution_logs = _consume_execution_logs(getattr(server, "sqlPlus", None))
        _log_daishansql_call(
            called=True,
            method="judgeQuery",
            request_payload={"query_q2": q2, "fixed_question": selected_question},
            sql_text=_extract_sql_texts_from_execution_logs(execution_logs),
            result=sql_result,
            sql_source="runtime",
        )
    except Exception as error:
        _log_daishansql_call(
            called=True,
            method="judgeQuery",
            request_payload={"query_q2": q2, "fixed_question": selected_question},
            sql_text="",
            result=None,
            sql_source="runtime",
            error=str(error),
            level="ERROR",
        )
        return await chat_with_category("通用", request)

    merged_question = f"{mapped_prompt}\n\n{str(sql_result)}\n\n{request.question}"
    updated_request = _build_chat_request_with_question(request, merged_question)
    return await chat_with_category("通用", updated_request)


def _extract_questions_for_sql(text_input: str, result_items: list[dict]) -> list[str]:
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

    return questions


def _extract_question_from_qa_text(question_text: str) -> str:
    if not isinstance(question_text, str):
        return ""

    if question_text.startswith("Question: "):
        parts = question_text.split("\tAnswer: ", 1)
        if parts and parts[0].startswith("Question: "):
            extracted = parts[0][10:].strip()
            return extracted

    return ""


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
    except FileNotFoundError:
        _prompt_mapping_cache[mapping_type] = {}
    except Exception:
        _prompt_mapping_cache[mapping_type] = {}

    return _prompt_mapping_cache[mapping_type]


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

    return prompt_text


def _clear_prompt_mapping_cache() -> None:
    _prompt_mapping_cache.clear()


def _find_type1_mapping_by_question(question: str) -> str:
    return _find_mapping_prompt_by_question(
        mapping_type="type1",
        mapping_path=_TYPE1_PROMPT_MAPPING_PATH,
        question=question,
    )


def _find_type2_mapping_by_question(question: str) -> str:
    return _find_mapping_prompt_by_question(
        mapping_type="type2",
        mapping_path=_TYPE2_PROMPT_MAPPING_PATH,
        question=question,
    )


def _find_type3_prompt_by_question(question: str) -> str:
    return _find_mapping_prompt_by_question(
        mapping_type="type3",
        mapping_path=_TYPE3_PROMPT_MAPPING_PATH,
        question=question,
    )


async def _post_process_type1(result_dict: dict) -> dict:
    result_items = result_dict.get("results", [])
    first_question = result_items[0].get("question", "") if result_items else ""
    kb_match = re.search(r"\[knowledgebase:(\w+)\]", first_question)

    if not kb_match:
        _log_daishansql_call(called=False, reason="kb_not_found")
        return {"type": 1, "data": {"kb_name": "园区知识库", "sql_result": "1"}}

    kb_name = kb_match.group(1)

    result = ""
    if kb_name == "园区知识库":
        _log_daishansql_call(called=False, reason="park_kb_shortcut")
        result = "1"
    elif kb_name == "企业知识库":
        server = _get_server()
        _consume_execution_logs(getattr(server, "sqlFixed", None))
        try:
            result = server.sqlFixed.sql_ChemicalCompanyInfo()
            execution_logs = _consume_execution_logs(getattr(server, "sqlFixed", None))
            _log_daishansql_call(
                called=True,
                method="sql_ChemicalCompanyInfo",
                sql_text=_extract_sql_texts_from_execution_logs(execution_logs),
                result=result,
                sql_source="runtime",
            )
        except Exception as error:
            _log_daishansql_call(
                called=True,
                method="sql_ChemicalCompanyInfo",
                sql_text="",
                result=None,
                sql_source="runtime",
                error=str(error),
                level="ERROR",
            )
            raise
    elif kb_name == "安全信息知识库":
        server = _get_server()
        _consume_execution_logs(getattr(server, "sqlFixed", None))
        try:
            result = server.sqlFixed.sql_SecuritySituation()
            execution_logs = _consume_execution_logs(getattr(server, "sqlFixed", None))
            _log_daishansql_call(
                called=True,
                method="sql_SecuritySituation",
                sql_text=_extract_sql_texts_from_execution_logs(execution_logs),
                result=result,
                sql_source="runtime",
            )
        except Exception as error:
            _log_daishansql_call(
                called=True,
                method="sql_SecuritySituation",
                sql_text="",
                result=None,
                sql_source="runtime",
                error=str(error),
                level="ERROR",
            )
            raise
    else:
        _log_daishansql_call(called=False, reason=f"unsupported_kb:{kb_name}")

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
        _log_daishansql_call(called=False, reason="type1_prompt_unavailable")
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

    try:
        sql_result = await asyncio.to_thread(
            _get_server().get_sql_result,
            query=text_input,
            history=[],
            questions=questions,
        )
        _log_daishansql_call(
            called=True,
            method="get_sql_result",
            request_payload={"query": text_input, "history": [], "questions": questions},
            sql_text=_extract_sql_texts_from_agent_result(sql_result),
            result=sql_result,
            sql_source="response",
        )
    except Exception as error:
        _log_daishansql_call(
            called=True,
            method="get_sql_result",
            request_payload={"query": text_input, "history": [], "questions": questions},
            sql_text="",
            result=None,
            sql_source="response",
            error=str(error),
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
        _log_daishansql_call(called=False, reason="type2_prompt_unavailable")
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
        _log_daishansql_call(called=False, method="judgeQuery", reason="type3_prompt_unavailable")
        return None

    server = _get_server()
    _consume_execution_logs(getattr(server, "sqlPlus", None))
    try:
        judge_result = await asyncio.to_thread(
            server.judgeQuery,
            request.question,
            return_question,
        )
        execution_logs = _consume_execution_logs(getattr(server, "sqlPlus", None))
        _log_daishansql_call(
            called=True,
            method="judgeQuery",
            request_payload={"query": request.question, "return_question": return_question},
            sql_text=_extract_sql_texts_from_execution_logs(execution_logs),
            result=judge_result,
            sql_source="runtime",
        )
    except Exception as error:
        _log_daishansql_call(
            called=True,
            method="judgeQuery",
            request_payload={"query": request.question, "return_question": return_question},
            sql_text="",
            result=None,
            sql_source="runtime",
            error=str(error),
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


async def handle_chat_general(
    request: ChatRequest,
    intent_service,
    chat_with_category: Callable[[str, ChatRequest], Awaitable[Any]],
):
    """General chat flow based on fixed-question single-table matching."""

    user_id = request.user_id or "anonymous"
    q1, q2 = await _build_query_variants(request.question)

    try:
        all_candidates = await query_fixed_question_candidates(
            intent_service=intent_service,
            query=q1,
            user_id=user_id,
        )
        top_candidates = select_top_candidates(
            candidates=all_candidates,
            min_similarity=float(settings.intent.fixed_question_similarity_threshold),
            top_k=int(settings.intent.fixed_question_top_k),
        )
        marker(
            "chat_general.ragflow_result",
            _build_ragflow_result_log(
                original_question=request.question,
                q1=q1,
                q2=q2,
                all_candidates=all_candidates,
            ),
        )

        selected_candidate, decision_log = await _pick_fixed_question_candidate(
            original_question=request.question,
            candidates=top_candidates,
        )
        marker(
            "chat_general.intent_decision",
            decision_log,
            level="WARNING" if decision_log.get("decision") == "fallback" else "INFO",
        )
        if selected_candidate is None:
            _log_daishansql_call(
                called=False,
                reason=str(decision_log.get("reason", "") or "no_fixed_question_selected"),
                request_payload={"query": request.question, "q1": q1, "q2": q2},
            )
            return await _route_low_confidence_to_general(request, chat_with_category)

        return await _route_selected_fixed_question(
            request=request,
            q2=q2,
            selected_question=str(selected_candidate.get("question", "") or ""),
            chat_with_category=chat_with_category,
        )
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
