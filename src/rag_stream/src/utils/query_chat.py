"""Query chat utilities for query rewriting and candidate reranking."""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from openai import OpenAI

from rag_stream.config.settings import QueryChatConfig, settings
from rag_stream.utils.log_manager_import import marker


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
    def _validate_content(text: str, original: str) -> tuple[bool, str]:
        """验证 AI 返回的内容是否有效。

        Returns:
            (is_valid, reason) 元组
        """
        if not text:
            return False, "empty"

        # 检测 JSON 格式（AI 错误返回）
        if text.strip().startswith(("{", "[")):
            return False, "json"

        # 检测指令性文字（AI 在解释而非改写）
        instruction_keywords = ["请", "应该", "建议", "需要", "可以"]
        if any(kw in text for kw in instruction_keywords):
            # 但排除原句本身就包含这些词的情况
            if not any(kw in original for kw in instruction_keywords):
                return False, "instruction"

        # 检测多行文本（可能包含解释）
        if "\n" in text and len(text.split("\n")) > 2:
            return False, "multiline"

        return True, ""

    def rewrite_query_remove_company(self, query: str) -> str:
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

        marker("query_chat.attempt", {"query_len": len(source_query)})
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self._config.model,
                temperature=self._config.temperature,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是中文问句清洗助手。"
                            "只做一件事：删除用户句子中的企业名称和园区/开发区名称。"
                            "需要删除的内容包括：企业名称（如XX公司、XX集团）、园区名称（如岱山经开区、经开区、岱山经济开发区、岱山开发区等）。"
                            "除上述名称外，保留原句其余内容和语义，不要扩写，不要解释。"
                            "只返回清洗后的单句文本。"
                        ),
                    },
                    {"role": "user", "content": source_query},
                ],
            )
            rewritten = self._extract_text_content(response).strip()
        except Exception as error:
            marker("query_chat.api_error", {"error": str(error)}, level="ERROR")
            raise

        if not rewritten:
            marker("query_chat.empty_response", {}, level="WARNING")
            return query

        # 内容验证
        is_valid, reason = self._validate_content(rewritten, query)
        if not is_valid:
            marker(
                "query_chat.content_invalid",
                {"reason": reason, "response_preview": rewritten[:100]},
                level="WARNING",
            )
            return query  # 回退原句

        marker("query_chat.success", {"output_len": len(rewritten)})
        return rewritten

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
        normalized_candidates = [str(item or "").strip() for item in candidates if str(item or "").strip()]
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
    """异步改写 query，删除企业名称。

    Args:
        query: 原始查询字符串
        config: QueryChat 配置对象

    Returns:
        改写后的字符串，失败时返回原 query
    """
    # 输入验证
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

    # 使用 asyncio.to_thread 包装同步调用
    try:
        chat = QueryChat(config)
        result = await asyncio.to_thread(
            chat.rewrite_query_remove_company, source_query
        )
        return result
    except Exception:
        # 任何异常都返回原 query（降级）
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
