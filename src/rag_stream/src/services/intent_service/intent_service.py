"""
IntentService - 意图识别服务
负责处理三种意图类型(Type 0/1/2)的业务逻辑
"""

from typing import Any, Dict, List

from log_decorator import log
from src.services.intent_service.base_intent_service import (
    BaseIntentService,
    IntentRecognizerSettings,
    IntentResult,
)


class IntentService(BaseIntentService):
    """意图识别服务"""

    @log()
    async def process_query(self, text_input: str, user_id: str) -> dict:
        return await super().process_query(text_input, user_id)

    @staticmethod
    def _judge_daishan_intent_priority(table_results, recognizer_settings):
        """
        岱山优先级判断逻辑：
        1) 优先看【岱山-指令集】最大相似度，若 >= 阈值则直接返回其最佳结果
        2) 否则返回【岱山-数据库问题】最佳结果（若存在）
        3) 都无结果则返回 None
        """
        instruction_table = "岱山-指令集"
        db_question_table = "岱山-数据库问题"

        instruction_results = table_results.get(instruction_table, [])
        if instruction_results:
            best_instruction = max(
                instruction_results,
                key=lambda item: float(getattr(item, "total_similarity", 0.0) or 0.0),
            )
            if float(getattr(best_instruction, "total_similarity", 0.0) or 0.0) >= float(
                recognizer_settings.similarity_threshold
            ):
                return best_instruction

        db_results = table_results.get(db_question_table, [])
        if db_results:
            return max(
                db_results,
                key=lambda item: float(getattr(item, "total_similarity", 0.0) or 0.0),
            )

        return None

    @staticmethod
    def _should_use_daishan_priority(recognizer_settings) -> bool:
        """仅在存在岱山双表映射时启用优先级规则"""
        mapping_keys = set(recognizer_settings.database_mapping.keys())
        return {"岱山-指令集", "岱山-数据库问题"}.issubset(mapping_keys)

    def __init__(self, ragflow_client):
        super().__init__(ragflow_client=ragflow_client)

    @log()
    def _load_process_settings(self) -> IntentRecognizerSettings:
        return self._load_intent_recognizer_settings()

    @log()
    async def _query_process_table_results(
        self,
        text_input: str,
        recognizer_settings: IntentRecognizerSettings,
    ) -> Dict[str, List[Any]]:
        return await self._query_table_results(
            query=text_input,
            recognizer_settings=recognizer_settings,
        )

    @log()
    def _sort_process_table_results(
        self,
        table_results: Dict[str, List[Any]],
        recognizer_settings: IntentRecognizerSettings,
    ) -> List[Any]:
        return self._sort_table_results(
            table_results=table_results,
            recognizer_settings=recognizer_settings,
        )

    @log()
    def _get_process_judge_function(self):
        return self._judge_daishan_intent_priority

    @log()
    async def _post_process_result(self, intent_result: IntentResult) -> dict:
        return {
            "type": intent_result.type,
            "query": intent_result.query,
            "results": [
                {"question": item.question, "similarity": item.similarity}
                for item in intent_result.results
            ],
            "similarity": intent_result.similarity,
            "database": intent_result.database,
        }

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
