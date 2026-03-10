"""Guess-questions service built on fixed-question retrieval flow."""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any

from rag_stream.config.settings import settings
from rag_stream.services.fixed_question_flow_service import (
    query_fixed_question_candidates,
    replace_daishan_zone_alias,
)
from rag_stream.utils.dify_client_factory import get_client
from rag_stream.utils.log_manager_import import entry_trace, marker
from rag_stream.utils.prompts import GuessQuestionsPrompts
from rag_stream.utils.query_chat import rewrite_query


async def _rewrite_query_remove_company_with_fallback(query: str) -> str:
    if not isinstance(query, str) or not query:
        return query

    if not settings.query_chat.enabled:
        return query

    if (
        not (settings.query_chat.api_key or "").strip()
        or not (settings.query_chat.base_url or "").strip()
    ):
        return query

    rewritten = await rewrite_query(query, settings.query_chat)
    rewritten_text = str(rewritten or "").strip()
    return rewritten_text or query


def _parse_llm_generated_questions(answer_text: str) -> list[str]:
    text = (answer_text or "").strip()
    if not text:
        return []

    candidates: list[str] = []

    json_text = text
    if "[" in text and "]" in text:
        json_text = text[text.find("[") : text.rfind("]") + 1]

    try:
        parsed = json.loads(json_text)
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, str):
                    value = item.strip()
                elif isinstance(item, dict):
                    value = str(
                        item.get("question") or item.get("guess_your_question") or ""
                    ).strip()
                else:
                    value = str(item).strip()

                if value:
                    candidates.append(value)
    except json.JSONDecodeError:
        for line in text.splitlines():
            normalized = re.sub(r"^\s*(?:[-*]|\d+[\.\)\、\:]?)\s*", "", line).strip()
            if normalized:
                candidates.append(normalized)

    deduplicated: list[str] = []
    seen = set()
    for item in candidates:
        if item not in seen:
            seen.add(item)
            deduplicated.append(item)

    return deduplicated[:3]


async def _generate_type2_fallback_questions(original_question: str) -> list[dict[str, str]]:
    try:
        general_client = get_client("GENRAL_CHAT")
    except Exception as error:
        marker("获取GENRAL_CHAT client失败", {"error": str(error)}, level="ERROR")
        return []

    prompt = GuessQuestionsPrompts.get_type2_fallback_prompt(original_question)

    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(
                general_client.run_chat,
                query=prompt,
                user="system",
                inputs={},
                conversation_id="",
            ),
            timeout=float(settings.query_chat.timeout),
        )
    except asyncio.TimeoutError:
        marker("调用GENRAL_CHAT生成猜你想问超时", {"timeout": settings.query_chat.timeout}, level="ERROR")
        return []
    except Exception as error:
        marker("调用GENRAL_CHAT生成猜你想问失败", {"error": str(error)}, level="ERROR")
        return []

    answer_text = response.answer if hasattr(response, "answer") else str(response)
    generated = _parse_llm_generated_questions(answer_text)

    return [{"question": item} for item in generated]


@entry_trace("guess-questions")
async def handle_guess_questions(question: str, intent_service) -> list[dict[str, str]]:
    try:
        normalized_question = str(question or "").strip()
        if not normalized_question:
            return []

        if len(normalized_question) > 1000:
            return []

        q2 = replace_daishan_zone_alias(normalized_question)
        q1 = await _rewrite_query_remove_company_with_fallback(q2)

        candidates = await query_fixed_question_candidates(
            intent_service=intent_service,
            query=q1,
            user_id="anonymous",
        )

        top_candidates = candidates[: max(int(settings.intent.fixed_question_top_k), 1)]
        questions = [
            {"question": str(item.get("question", "") or "").strip()}
            for item in top_candidates
            if str(item.get("question", "") or "").strip()
        ][:3]

        if questions:
            return questions

        return await _generate_type2_fallback_questions(normalized_question)
    except Exception as error:
        marker("猜你想问服务异常", {"error": str(error)}, level="ERROR")
        return []
