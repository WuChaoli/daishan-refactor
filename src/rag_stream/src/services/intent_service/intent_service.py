"""
IntentService - 意图识别服务
负责处理意图类型(Type 0/1/2/3)的业务逻辑
"""

import dataclasses
from typing import Any, Dict, List, Optional

from rag_stream.config.settings import settings
from rag_stream.utils.log_manager_import import marker, trace
from rag_stream.services.intent_service.base_intent_service import (
    BaseIntentService,
    IntentRecognizerSettings,
    IntentResult,
)


class _DefaultIntentCandidate:
    """Sentinel candidate used to force fallback to default intent type."""

    database = ""
    question = ""
    total_similarity = 0.0


class IntentService(BaseIntentService):
    """意图识别服务"""

    def __init__(self, ragflow_client):
        super().__init__(ragflow_client=ragflow_client)
        self._intent_classifier: Optional[Any] = None

        # 初始化分类器（如果启用）
        if settings.intent_classification.enabled:
            try:
                from rag_stream.utils.intent_classifier import IntentClassifier

                self._intent_classifier = IntentClassifier(
                    settings.intent_classification
                )
                marker("intent_classifier.initialized", {"enabled": True})
            except Exception as e:
                marker(
                    "intent_classifier.init_failed",
                    {"error": str(e)},
                    level="WARNING",
                )
                self._intent_classifier = None

    async def process_query(self, text_input: str, user_id: str) -> dict:
        return await super().process_query(text_input, user_id)

    @staticmethod
    def _judge_daishan_intent_priority(table_results, recognizer_settings):
        """
        岱山优先级判断逻辑：
        1) 优先判断【岱山-指令集】和【岱山-指令集-固定问题】中的最高相似度结果
        2) 若该结果 >= priority_similarity_threshold，则直接返回
        3) 否则仅在【岱山-数据库问题】中取最高相似度结果（不过 similarity_threshold）
        4) 若【岱山-数据库问题】无结果，则返回默认类型哨兵结果
        """
        instruction_table = "岱山-指令集"
        fixed_instruction_table = "岱山-指令集-固定问题"
        db_question_table = "岱山-数据库问题"
        priority_threshold = float(recognizer_settings.priority_similarity_threshold)

        marker(
            "岱山优先级判断启动",
            {
                "priority_threshold": priority_threshold,
                "tables": [instruction_table, fixed_instruction_table],
                "fallback_table": db_question_table,
            },
        )

        # 第一步：收集优先级候选结果
        priority_candidates = []
        for table_name in (instruction_table, fixed_instruction_table):
            table_items = table_results.get(table_name, [])
            if table_items:
                best_in_table = max(table_items, key=BaseIntentService._safe_similarity)
                best_similarity = BaseIntentService._safe_similarity(best_in_table)
                priority_candidates.append(best_in_table)
                marker(
                    "优先表最高相似度",
                    {
                        "table": table_name,
                        "similarity": best_similarity,
                        "question_preview": getattr(best_in_table, "question", "")[:50],
                    },
                )

        # 第二步：判断优先级候选是否满足阈值
        if priority_candidates:
            best_priority = max(
                priority_candidates, key=BaseIntentService._safe_similarity
            )
            best_priority_similarity = BaseIntentService._safe_similarity(best_priority)

            marker(
                "优先级最佳候选",
                {
                    "similarity": best_priority_similarity,
                    "threshold": priority_threshold,
                    "satisfied": best_priority_similarity >= priority_threshold,
                },
            )

            if best_priority_similarity >= priority_threshold:
                return best_priority

        # 第三步：仅在【岱山-数据库问题】中筛选最高相似度（不过 similarity_threshold）
        db_question_results = table_results.get(db_question_table, [])
        if db_question_results:
            best_db_question = max(
                db_question_results, key=BaseIntentService._safe_similarity
            )
            best_db_similarity = BaseIntentService._safe_similarity(best_db_question)
            marker(
                "数据库问题表最高相似度",
                {
                    "table": db_question_table,
                    "similarity": best_db_similarity,
                    "question_preview": getattr(best_db_question, "question", "")[:50],
                },
            )
            return best_db_question

        marker(
            "数据库问题表无结果，回默认类型",
            {"table": db_question_table},
            level="WARNING",
        )
        return _DefaultIntentCandidate()

    def _load_process_settings(
        self, text_input: Optional[str] = None
    ) -> IntentRecognizerSettings:
        recognizer_settings = self._load_intent_recognizer_settings()

        # 分类驱动检索（Phase 6）
        if text_input and self._intent_classifier:
            classification_result = self._intent_classifier.classify(text_input)
            threshold = settings.intent_classification.confidence_threshold

            # 降级或低置信度时，保持全量检索
            if classification_result.degraded:
                marker(
                    "classifier.degraded_fallback",
                    {"query": text_input, "reason": "degraded"},
                )
                return recognizer_settings

            if classification_result.confidence < threshold:
                marker(
                    "classifier.low_confidence_fallback",
                    {
                        "query": text_input,
                        "confidence": classification_result.confidence,
                        "threshold": threshold,
                    },
                )
                return recognizer_settings

            # 高置信度时，过滤 database_mapping
            type_id = classification_result.type_id
            filtered_mapping = {
                k: v
                for k, v in recognizer_settings.database_mapping.items()
                if v == type_id
            }

            if filtered_mapping:  # 有匹配的库
                # 创建新的 IntentRecognizerSettings 实例（保持不可变性）
                recognizer_settings = dataclasses.replace(
                    recognizer_settings, database_mapping=filtered_mapping
                )
            # else: 没有匹配的库，保持原映射（防御性编程）

        return recognizer_settings

    async def _query_process_table_results(
        self,
        text_input: str,
        recognizer_settings: IntentRecognizerSettings,
    ) -> Dict[str, List[Any]]:
        return await self._query_table_results(
            query=text_input,
            recognizer_settings=recognizer_settings,
        )

    def _sort_process_table_results(
        self,
        table_results: Dict[str, List[Any]],
        recognizer_settings: IntentRecognizerSettings,
    ) -> List[Any]:
        return self._sort_table_results(
            table_results=table_results,
            recognizer_settings=recognizer_settings,
        )

    def _get_process_judge_function(self):
        return self._judge_daishan_intent_priority

    async def _post_process_result(self, intent_result: IntentResult) -> dict:
        """使用基类默认实现，已包含 question 和 answer 字段"""
        return await super()._post_process_result(intent_result)

    # async def _query_dify_chat_blocking(
    #     self, client, query: str, user_id: str
    # ) -> str:
    #     """
    #     调用 Dify Chat 查询并返回同步结果

    #     Args:
    #         client: Dify Chat 客户端
    #         query: 查询文本
    #         user_id: 用户 ID

    #     Returns:
    #         查询结果字符串
    #     """
    #     try:
    #         # 调用 Dify Chat API
    #         response = client.create_chat_message(
    #             query=query,
    #             user=user_id,
    #             response_mode="blocking",
    #         )

    #         # 解析响应
    #         if hasattr(response, "answer"):
    #             return response.answer
    #         else:
    #             return str(response)

    #     except Exception as e:
    #         logger.error(f"Dify Chat 查询异常: {str(e)}", exc_info=True)
    #         return f"Dify Chat 查询异常: {str(e)}"
