"""意图分类服务：使用 LLM 进行粗粒度意图分类。"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from src.config.settings import IntentClassificationConfig, settings
from src.utils.log_manager_import import marker


@dataclass
class ClassificationResult:
    """分类结果数据类。"""

    type_id: int  # 1/2/3
    confidence: float  # 0.0-1.0
    raw_response: str  # 原始响应
    degraded: bool  # 是否降级


class IntentClassifier:
    """意图分类器，使用 LLM 进行粗粒度分类。"""

    def __init__(self, config: IntentClassificationConfig):
        self._config = config
        self._client: OpenAI | None = None

    def _build_client(self) -> OpenAI:
        """构建 OpenAI 客户端。"""
        base_url_set = bool((self._config.base_url or "").strip())
        api_key_set = bool((self._config.api_key or "").strip())
        model_set = bool((self._config.model or "").strip())

        if not base_url_set or not api_key_set or not model_set:
            marker(
                "classifier.config_invalid",
                {
                    "base_url_set": base_url_set,
                    "api_key_set": api_key_set,
                    "model_set": model_set,
                },
                level="ERROR",
            )
            raise ValueError("intent_classification 配置不完整，请检查 base_url/api_key/model")

        return OpenAI(
            base_url=self._config.base_url,
            api_key=self._config.api_key,
            timeout=self._config.timeout,
        )

    def _get_client(self) -> OpenAI:
        """获取或初始化客户端。"""
        if self._client is None:
            self._client = self._build_client()
            marker(
                "classifier.client_initialized",
                {
                    "timeout": self._config.timeout,
                    "temperature": self._config.temperature,
                },
            )
        return self._client

    def _build_prompt(self, query: str) -> list[dict[str, str]]:
        """构建分类 prompt。"""
        return [
            {
                "role": "system",
                "content": (
                    "你是问题分类助手。请根据用户的问题，判断其属于以下哪种类型：\n\n"
                    "1 - 岱山-指令集\n"
                    "2 - 岱山-数据库问题\n"
                    "3 - 岱山-指令集-固定问题\n\n"
                    "只返回 JSON 格式：{\"type\": 数字编号, \"confidence\": 置信度(0.0-1.0)}，不要添加其他说明。"
                ),
            },
            {"role": "user", "content": query},
        ]

    def _parse_classification_result(self, raw_response: str) -> tuple[int, float]:
        """解析 JSON 响应，提取 type_id 和 confidence。"""
        try:
            data = json.loads(raw_response)
            type_id = int(data.get("type", 0))
            confidence = float(data.get("confidence", 0.0))
            return type_id, confidence
        except (json.JSONDecodeError, ValueError, TypeError):
            marker(
                "classifier.json_parse_error",
                {"raw": raw_response[:100]},
                level="WARNING",
            )
            raise ValueError("无法解析分类响应")

    def _validate_classification_result(self, type_id: int, confidence: float) -> bool:
        """验证分类结果是否有效。"""
        valid_type_id = type_id in {1, 2, 3}
        valid_confidence = 0.0 <= confidence <= 1.0
        return valid_type_id and valid_confidence

    def _get_degraded_result(self) -> ClassificationResult:
        """返回降级结果。"""
        return ClassificationResult(
            type_id=0,
            confidence=0.0,
            raw_response="",
            degraded=True,
        )

    def classify(self, query: str) -> ClassificationResult:
        """分类用户 query。

        Args:
            query: 用户查询字符串

        Returns:
            ClassificationResult: 分类结果
        """
        # 功能禁用，直接返回降级结果
        if not self._config.enabled:
            marker("classifier.disabled", {})
            return self._get_degraded_result()

        # 输入验证
        if not isinstance(query, str):
            marker(
                "classifier.invalid_input",
                {"input_type": type(query).__name__},
                level="WARNING",
            )
            return self._get_degraded_result()

        source_query = query.strip()
        if not source_query:
            marker("classifier.empty_query", level="WARNING")
            return self._get_degraded_result()

        marker("classifier.attempt", {"query_len": len(source_query)})

        try:
            # 超时降级：使用 asyncio.wait_for 包装 LLM 调用
            try:
                client = self._get_client()
                response = asyncio.run(
                    asyncio.wait_for(
                        asyncio.to_thread(
                            client.chat.completions.create,
                            model=self._config.model,
                            temperature=self._config.temperature,
                            messages=self._build_prompt(source_query),
                        ),
                        timeout=self._config.timeout,
                    )
                )
            except asyncio.TimeoutError:
                marker("classifier.timeout", {}, level="WARNING")
                return self._get_degraded_result()

            # 提取响应内容
            raw_response = ""
            if response and hasattr(response, "choices") and response.choices:
                message = response.choices[0].message
                content = getattr(message, "content", "")
                if isinstance(content, str):
                    raw_response = content.strip()

            if not raw_response:
                marker("classifier.empty_response", {}, level="WARNING")
                return self._get_degraded_result()

            # 解析 JSON 响应
            try:
                type_id, confidence = self._parse_classification_result(raw_response)
            except ValueError:
                marker(
                    "classifier.invalid_response",
                    {"reason": "json_parse_error", "raw": raw_response[:100]},
                    level="WARNING",
                )
                return self._get_degraded_result()

            # 验证分类结果
            if not self._validate_classification_result(type_id, confidence):
                reason_parts = []
                if type_id not in {1, 2, 3}:
                    reason_parts.append(f"invalid_type_id={type_id}")
                if not (0.0 <= confidence <= 1.0):
                    reason_parts.append(f"invalid_confidence={confidence}")
                reason = ", ".join(reason_parts)

                marker(
                    "classifier.invalid_response",
                    {"reason": reason, "raw": raw_response[:100]},
                    level="WARNING",
                )
                return self._get_degraded_result()

            # 分类成功
            marker(
                "classifier.success",
                {"type_id": type_id, "confidence": confidence},
            )
            return ClassificationResult(
                type_id=type_id,
                confidence=confidence,
                raw_response=raw_response,
                degraded=False,
            )

        # API 错误降级：捕获所有异常
        except Exception as error:
            marker(
                "classifier.error",
                {"error": str(error)},
                level="ERROR",
            )
            return self._get_degraded_result()


# 全局分类器实例
_classifier_instance: IntentClassifier | None = None


def get_intent_classifier() -> IntentClassifier:
    """获取全局意图分类器实例。"""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = IntentClassifier(settings.intent_classification)
    return _classifier_instance


def classify_intent(query: str) -> ClassificationResult:
    """分类用户 query 的便捷函数。"""
    return get_intent_classifier().classify(query)
