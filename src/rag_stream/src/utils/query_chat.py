"""Query 聊天工具：用于 query 预处理（企业名称清理）。"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from openai import OpenAI

from src.config.settings import QueryChatConfig, settings
from src.utils.log_manager_import import marker


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

        marker("query_chat.request_start", {"query_len": len(source_query)})
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
                            "只做一件事：删除用户句子中的企业名称。"
                            "除企业名称外，保留原句其余内容和语义，不要扩写，不要解释。"
                            "只返回清洗后的单句文本。"
                        ),
                    },
                    {"role": "user", "content": source_query},
                ],
            )
            rewritten = self._extract_text_content(response).strip()
        except Exception as error:
            marker("query_chat.request_failed", {"error": str(error)}, level="ERROR")
            raise

        if not rewritten:
            marker("query_chat.empty_response", {}, level="WARNING")
            return query
        marker(
            "query_chat.request_complete",
            {"output_len": len(rewritten), "normalized": rewritten != query},
        )
        return rewritten


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
