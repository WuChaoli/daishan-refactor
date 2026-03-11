from __future__ import annotations

from typing import Any, Iterable

from rag_stream.config.settings import settings
from rag_stream.utils.log_manager_import import marker, trace


DAISHAN_ZONE_ALIAS = "岱山经开区"
PARK_ALIAS = "园区"


@trace
def replace_daishan_zone_alias(query: str) -> str:
    if not isinstance(query, str):
        return query
    if not query:
        return query
    return query.replace(DAISHAN_ZONE_ALIAS, PARK_ALIAS)


@trace
def extract_question_from_qa_text(question_text: str) -> str:
    if not isinstance(question_text, str):
        return ""

    if question_text.startswith("Question: "):
        parts = question_text.split("\tAnswer: ", 1)
        if parts and parts[0].startswith("Question: "):
            return parts[0][10:].strip()

    return ""


@trace
def normalize_fixed_question_candidates(raw_candidates: Iterable[Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []

    for item in raw_candidates or []:
        if isinstance(item, dict):
            raw_question = _clean_fixed_question_text(item.get("question", ""))
            similarity_value = item.get("similarity", 0.0)
        else:
            raw_question = _clean_fixed_question_text(getattr(item, "question", ""))
            similarity_value = getattr(item, "similarity", 0.0)

        if not raw_question:
            continue

        try:
            similarity = float(similarity_value)
        except (TypeError, ValueError):
            similarity = 0.0

        question = extract_question_from_qa_text(raw_question) or raw_question
        normalized.append(
            {
                "question": question.strip(),
                "raw_question": raw_question,
                "similarity": similarity,
            }
        )

    normalized.sort(key=lambda candidate: float(candidate.get("similarity", 0.0)), reverse=True)
    return normalized


@trace
def select_top_candidates(
    candidates: list[dict[str, Any]],
    min_similarity: float,
    top_k: int,
) -> list[dict[str, Any]]:
    effective_top_k = max(int(top_k), 1)
    filtered = [
        item
        for item in candidates
        if float(item.get("similarity", 0.0)) >= float(min_similarity)
    ]
    return filtered[:effective_top_k]


@trace
async def query_fixed_question_candidates(
    intent_service: Any,
    query: str,
    user_id: str,
) -> list[dict[str, Any]]:
    top_k = int(settings.intent.fixed_question_top_k)
    table_name = str(settings.intent.fixed_question_table_name)

    raw_candidates: list[dict[str, Any]] = []
    if hasattr(intent_service, "query_fixed_question_candidates"):
        raw_candidates = await intent_service.query_fixed_question_candidates(
            query,
            top_k=top_k,
            table_name=table_name,
        )
    else:
        marker(
            "fixed_question_query_fallback_process_query",
            {"table_name": table_name},
            level="WARNING",
        )
        result_dict = await intent_service.process_query(query, user_id)
        raw_candidates = result_dict.get("results", []) if isinstance(result_dict, dict) else []

    return normalize_fixed_question_candidates(raw_candidates)
