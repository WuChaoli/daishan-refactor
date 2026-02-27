"""
IntentService - 意图识别服务
负责处理意图类型(Type 0/1/2/3)的业务逻辑
"""

from typing import Any, Dict, List

from rag_stream.utils.log_manager_import import marker, trace
from rag_stream.services.intent_service.base_intent_service import (
    BaseIntentService,
    IntentRecognizerSettings,
    IntentResult,
)


class IntentService(BaseIntentService):
    """意图识别服务"""

    def __init__(self, ragflow_client):
        super().__init__(ragflow_client=ragflow_client)
        self._use_daishan_priority = False

    async def process_query(self, text_input: str, user_id: str) -> dict:
        return await super().process_query(text_input, user_id)

    @staticmethod
    def _judge_daishan_intent_priority(table_results, recognizer_settings):
        """
        岱山优先级判断逻辑：
        1) 优先判断【岱山-指令集】和【岱山-指令集-固定问题】中的最高相似度结果
        2) 若该结果 >= priority_similarity_threshold，则直接返回
        3) 否则在所有返回结果中取全局最高相似度结果
        """
        instruction_table = "岱山-指令集"
        fixed_instruction_table = "岱山-指令集-固定问题"
        priority_threshold = float(recognizer_settings.priority_similarity_threshold)

        marker("岱山优先级判断启动", {"priority_threshold": priority_threshold, "tables": [instruction_table, fixed_instruction_table]})

        # 第一步：收集优先级候选结果
        priority_candidates = []
        for table_name in (instruction_table, fixed_instruction_table):
            table_items = table_results.get(table_name, [])
            if table_items:
                best_in_table = max(table_items, key=BaseIntentService._safe_similarity)
                best_similarity = BaseIntentService._safe_similarity(best_in_table)
                priority_candidates.append(best_in_table)
                marker("优先表最高相似度", {"table": table_name, "similarity": best_similarity, "question_preview": getattr(best_in_table, "question", "")[:50]})

        # 第二步：判断优先级候选是否满足阈值
        if priority_candidates:
            best_priority = max(priority_candidates, key=BaseIntentService._safe_similarity)
            best_priority_similarity = BaseIntentService._safe_similarity(best_priority)

            marker("优先级最佳候选", {
                "similarity": best_priority_similarity,
                "threshold": priority_threshold,
                "satisfied": best_priority_similarity >= priority_threshold
            })

            if best_priority_similarity >= priority_threshold:
                return best_priority

        # 第三步：全局筛选最高相似度
        all_results = []
        for table_items in table_results.values():
            all_results.extend(table_items)

        if all_results:
            global_best = max(all_results, key=BaseIntentService._safe_similarity)
            global_best_similarity = BaseIntentService._safe_similarity(global_best)
            global_best_table = getattr(global_best, "database", "未知")

            marker("全局最高相似度", {
                "similarity": global_best_similarity,
                "database": global_best_table,
                "question_preview": getattr(global_best, "question", "")[:50]
            })
            return global_best

        marker("所有知识库均无检索结果", {}, level="WARNING")
        return None

    @staticmethod
    def _should_use_daishan_priority(recognizer_settings) -> bool:
        """仅在存在岱山指令双表映射时启用优先级规则"""
        mapping_keys = set(recognizer_settings.database_mapping.keys())
        return {"岱山-指令集", "岱山-指令集-固定问题"}.issubset(mapping_keys)

    def _load_process_settings(self) -> IntentRecognizerSettings:
        recognizer_settings = self._load_intent_recognizer_settings()
        self._use_daishan_priority = self._should_use_daishan_priority(
            recognizer_settings
        )
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
        if self._use_daishan_priority:
            return self._judge_daishan_intent_priority
        return None

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
