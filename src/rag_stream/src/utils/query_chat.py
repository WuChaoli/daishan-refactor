"""Query chat utilities for query rewriting and candidate reranking."""

from __future__ import annotations

import asyncio
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from openai import OpenAI

from rag_stream.config.settings import QueryChatConfig, settings
from rag_stream.utils.log_manager_import import marker

_ALLOWED_PLACEHOLDER_TOKENS = {"某公司", "某人", "某证书"}
def _build_sql_plus_candidate_paths() -> tuple[Path, ...]:
    current_root = Path(__file__).resolve().parents[4]
    candidates = [
        current_root / "src" / "DaiShanSQL" / "DaiShanSQL" / "SQL" / "sql_Plus.py"
    ]

    if ".worktrees" in current_root.parts:
        worktrees_index = current_root.parts.index(".worktrees")
        main_root = Path(*current_root.parts[:worktrees_index])
        candidates.append(
            main_root / "src" / "DaiShanSQL" / "DaiShanSQL" / "SQL" / "sql_Plus.py"
        )

    unique_candidates: list[Path] = []
    for candidate in candidates:
        if candidate not in unique_candidates:
            unique_candidates.append(candidate)
    return tuple(unique_candidates)


@lru_cache(maxsize=1)
def _load_qualification_terms() -> tuple[str, ...]:
    candidate_paths = _build_sql_plus_candidate_paths()

    for candidate_path in candidate_paths:
        try:
            source_text = candidate_path.read_text(encoding="utf-8")
        except Exception:
            continue

        match = re.search(r"qualifications\s*=\s*(\[[\s\S]*?\])", source_text)
        if not match:
            continue

        try:
            value = eval(match.group(1), {"__builtins__": {}}, {})
        except Exception as error:
            marker(
                "query_chat.qualification_terms_parse_failed",
                {"error": str(error), "path": str(candidate_path)},
                level="WARNING",
            )
            return ()

        if isinstance(value, list):
            return tuple(str(item).strip() for item in value if str(item).strip())

    marker(
        "query_chat.qualification_terms_missing",
        {"paths": [str(path) for path in candidate_paths]},
        level="WARNING",
    )
    return ()


class QueryChat:
    """query 预处理聊天客户端封装。"""

    def __init__(self, config: QueryChatConfig):
        self._config = config
        self._client: Optional[OpenAI] = None

    def _build_client(self) -> OpenAI:
        base_url_set = bool((self._config.base_url or "").strip())
        api_key_set = bool((self._config.api_key or "").strip())
        model_set = bool((self._config.model or "").strip())

        if not base_url_set or not api_key_set or not model_set:
            marker(
                "query_chat.config_invalid",
                {
                    "base_url_set": base_url_set,
                    "api_key_set": api_key_set,
                    "model_set": model_set,
                },
                level="ERROR",
            )
            raise ValueError("query_chat 配置不完整，请检查 base_url/api_key/model")

        return OpenAI(
            base_url=self._config.base_url,
            api_key=self._config.api_key,
            timeout=self._config.timeout,
        )

    def _get_client(self) -> OpenAI:
        if self._client is None:
            self._client = self._build_client()
            marker(
                "query_chat.client_initialized",
                {
                    "timeout": self._config.timeout,
                    "temperature": self._config.temperature,
                },
            )
        return self._client

    @staticmethod
    def _extract_text_content(response: Any) -> str:
        if response is None or not getattr(response, "choices", None):
            return ""

        message = response.choices[0].message
        content = getattr(message, "content", "")

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            fragments: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text")
                    if text:
                        fragments.append(str(text))
                    continue

                text = getattr(item, "text", None)
                if text:
                    fragments.append(str(text))
            return "".join(fragments)

        return str(content or "")

    @staticmethod
    def _find_unsupported_placeholder_tokens(text: str) -> list[str]:
        sanitized = str(text or "")
        for token in _ALLOWED_PLACEHOLDER_TOKENS:
            sanitized = sanitized.replace(token, "")
        return ["某*"] if "某" in sanitized else []

    @classmethod
    def _validate_content(cls, text: str, original: str) -> tuple[bool, str]:
        """验证 AI 返回的内容是否有效。"""
        if not text:
            return False, "empty"

        stripped_text = text.strip()
        if stripped_text.startswith(("{", "[")):
            return False, "json"

        if "\n" in stripped_text or "\r" in stripped_text:
            return False, "multiline"

        instruction_keywords = ["请", "应该", "建议", "需要", "可以", "替换后", "说明"]
        if any(keyword in stripped_text for keyword in instruction_keywords):
            if not any(keyword in original for keyword in instruction_keywords):
                return False, "instruction"

        unsupported_tokens = cls._find_unsupported_placeholder_tokens(stripped_text)
        if unsupported_tokens:
            return False, "unsupported_placeholder"

        return True, ""

    @staticmethod
    def _normalize_model_output(text: str) -> str:
        return str(text or "").replace("\r", "").strip()

    def _build_placeholder_rewrite_prompt(self) -> str:
        qualification_terms = _load_qualification_terms()
        qualification_text = "、".join(qualification_terms)
        return (
            "你是中文问句占位改写助手。"
            "请在保持原句语义、顺序和语气不变的前提下，只做定向占位替换。"
            "替换规则："
            "1. 园区相关名称统一替换为‘园区’；"
            "2. 公司名称统一替换为‘某公司’；"
            "3. 人名统一替换为‘某人’；"
            "4. 证书、资质、许可证名称若命中给定词表则统一替换为‘某证书’。"
            "允许保留已有的‘园区/某公司/某人/某证书’，不要编号，不要扩写，不要解释，不要删除非目标信息。"
            "只返回改写后的单句文本。"
            f"证书词表：{qualification_text}"
        )

    def rewrite_query_with_placeholders(self, query: str) -> str:
        if not isinstance(query, str):
            marker(
                "query_chat.invalid_input",
                {"input_type": type(query).__name__},
                level="WARNING",
            )
            return ""

        source_query = query.strip()
        if not source_query:
            marker("query_chat.empty_query", {}, level="WARNING")
            return query

        marker("query_chat.request_start", {"query_len": len(source_query)})
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self._config.model,
                temperature=self._config.temperature,
                messages=[
                    {
                        "role": "system",
                        "content": self._build_placeholder_rewrite_prompt(),
                    },
                    {"role": "user", "content": source_query},
                ],
            )
            rewritten = self._normalize_model_output(self._extract_text_content(response))
        except Exception as error:
            marker("query_chat.request_failed", {"error": str(error)}, level="ERROR")
            raise

        if not rewritten:
            marker("query_chat.empty_response", {}, level="WARNING")
            return query

        is_valid, reason = self._validate_content(rewritten, source_query)
        if not is_valid:
            marker(
                "query_chat.content_invalid",
                {"reason": reason, "response_preview": rewritten[:100]},
                level="WARNING",
            )
            return query

        marker(
            "query_chat.request_complete",
            {"output_len": len(rewritten), "normalized": rewritten != source_query},
        )
        return rewritten

    def rewrite_query_remove_company(self, query: str) -> str:
        return self.rewrite_query_with_placeholders(query)

    @staticmethod
    def _resolve_candidate_from_response(response_text: str, candidates: list[str]) -> str:
        text = str(response_text or "").strip()
        if not text:
            return ""

        for candidate in candidates:
            if text == candidate:
                return candidate

        if text.isdigit():
            index = int(text) - 1
            if 0 <= index < len(candidates):
                return candidates[index]

        for candidate in candidates:
            if candidate in text:
                return candidate

        return ""

    def rerank_fixed_question_candidates(self, query: str, candidates: list[str]) -> str:
        normalized_query = str(query or "").strip()
        normalized_candidates = [
            str(item or "").strip() for item in candidates if str(item or "").strip()
        ]
        if not normalized_query or not normalized_candidates:
            return ""

        candidate_lines = "\n".join(
            f"{index + 1}. {candidate}"
            for index, candidate in enumerate(normalized_candidates)
        )
        marker(
            "query_chat.rerank_attempt",
            {"query_len": len(normalized_query), "candidates": len(normalized_candidates)},
        )
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self._config.model,
                temperature=self._config.temperature,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是候选问题匹配器。"
                            "请从候选问题中选择与用户问题最匹配的一条。"
                            "只返回候选原文或候选编号，不要输出解释。"
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"用户问题：{normalized_query}\n"
                            f"候选问题：\n{candidate_lines}"
                        ),
                    },
                ],
            )
            response_text = self._extract_text_content(response).strip()
        except Exception as error:
            marker("query_chat.rerank_failed", {"error": str(error)}, level="ERROR")
            raise

        selected = self._resolve_candidate_from_response(
            response_text=response_text,
            candidates=normalized_candidates,
        )
        marker("query_chat.rerank_success", {"matched": bool(selected)})
        return selected


_query_chat_instance: Optional[QueryChat] = None


def get_query_chat() -> QueryChat:
    global _query_chat_instance
    if _query_chat_instance is None:
        _query_chat_instance = QueryChat(settings.query_chat)
    return _query_chat_instance


async def rewrite_query(query: str, config: QueryChatConfig) -> str:
    """异步改写 query，输出占位后的 q1。"""
    if not isinstance(query, str):
        marker(
            "rewrite_query.invalid_input",
            {"input_type": type(query).__name__},
            level="WARNING",
        )
        return query

    source_query = query.strip()
    if not source_query:
        return query

    try:
        chat = QueryChat(config)
        result = await asyncio.to_thread(
            chat.rewrite_query_with_placeholders, source_query
        )
        return result
    except Exception:
        return query


def rewrite_query_remove_company(query: str) -> str:
    return get_query_chat().rewrite_query_remove_company(query)


async def rerank_fixed_question_candidates(
    query: str,
    candidates: list[str],
    config: QueryChatConfig,
) -> str:
    """Asynchronously rerank candidate fixed questions with a small chat model."""
    if not isinstance(query, str) or not query.strip():
        return ""
    if not isinstance(candidates, list) or not candidates:
        return ""

    try:
        chat = QueryChat(config)
        return await asyncio.to_thread(
            chat.rerank_fixed_question_candidates,
            query.strip(),
            candidates,
        )
    except Exception:
        return ""
