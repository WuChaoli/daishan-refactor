"""BaseIntentService - 意图识别流程抽象基类"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from log_decorator import logger
from src.config.settings import settings
from src.services.intent_recognizer import (
    IntentRecognizerSettings,
    JudgeFunction,
    load_intent_recognizer_settings_from_json,
    recognize_intent_from_results,
)
from src.services.ragflow_client import RagflowClient


@dataclass
class QueryResult:
    """查询结果"""

    question: str
    similarity: float


@dataclass
class IntentResult:
    """意图识别结果"""

    type: int
    query: str
    results: List[QueryResult]
    similarity: float
    database: str


class BaseIntentService(ABC):
    """意图识别服务抽象基类，定义统一识别流程"""

    def __init__(self, ragflow_client: RagflowClient):
        self.ragflow_client = ragflow_client

    async def process_query(self, text_input: str, user_id: str) -> dict:
        """模板方法：配置加载 -> 查表 -> 排序 -> 后处理"""
        try:
            recognizer_settings = self._load_process_settings(text_input, user_id)
            table_results = await self._query_process_table_results(
                text_input,
                user_id,
                recognizer_settings,
            )
            sorted_results = self._sort_process_table_results(
                text_input,
                user_id,
                table_results,
                recognizer_settings,
            )
            judge_function = self._get_process_judge_function(
                text_input,
                user_id,
                recognizer_settings,
            )
            intent_result = self._build_intent_result(
                query=text_input,
                sorted_results=sorted_results,
                recognizer_settings=recognizer_settings,
                judge_function=judge_function,
            )
            return await self._post_process_result(text_input, user_id, intent_result)
        except Exception as e:
            logger.error(f"处理查询异常: {str(e)}", exc_info=True)
            return self._build_process_error_result(e)

    @abstractmethod
    def _load_process_settings(
        self,
        text_input: str,
        user_id: str,
    ) -> IntentRecognizerSettings:
        """步骤1：加载意图识别配置"""

    @abstractmethod
    async def _query_process_table_results(
        self,
        text_input: str,
        user_id: str,
        recognizer_settings: IntentRecognizerSettings,
    ) -> Dict[str, List[Any]]:
        """步骤2：查询表结果"""

    @abstractmethod
    def _sort_process_table_results(
        self,
        text_input: str,
        user_id: str,
        table_results: Dict[str, List[Any]],
        recognizer_settings: IntentRecognizerSettings,
    ) -> List[Any]:
        """步骤3：排序表结果"""

    @abstractmethod
    async def _post_process_result(
        self,
        text_input: str,
        user_id: str,
        intent_result: IntentResult,
    ) -> dict:
        """步骤4：后处理并返回结果"""

    def _get_process_judge_function(
        self,
        text_input: str,
        user_id: str,
        recognizer_settings: IntentRecognizerSettings,
    ) -> Optional[JudgeFunction]:
        """可选步骤：提供自定义判断函数"""
        return None

    def _build_process_error_result(self, error: Exception) -> dict:
        """流程异常兜底返回"""
        return {"type": settings.intent.default_type, "data": {"error": str(error)}}

    def _load_intent_recognizer_settings(
        self,
        mapping_file: Optional[str] = None,
    ) -> IntentRecognizerSettings:
        """加载意图识别配置"""
        return load_intent_recognizer_settings_from_json(config_file=mapping_file)

    async def _query_table_results(
        self,
        query: str,
        recognizer_settings: IntentRecognizerSettings,
    ) -> Dict[str, List[Any]]:
        """并发查询映射中所有表"""
        if self.ragflow_client is None:
            raise ValueError("RagflowClient not initialized")

        if not hasattr(self.ragflow_client, "query_single_database"):
            raise ValueError("RagflowClient missing query_single_database method")

        table_names = list(recognizer_settings.database_mapping.keys())
        tasks = [
            self.ragflow_client.query_single_database(query, table_name)
            for table_name in table_names
        ]
        task_results = await asyncio.gather(*tasks, return_exceptions=True)

        table_results: Dict[str, List[Any]] = {}
        for table_name, task_result in zip(table_names, task_results):
            if isinstance(task_result, Exception):
                logger.warning(
                    "查询表失败: table=%s, error=%s",
                    table_name,
                    str(task_result),
                )
                table_results[table_name] = []
                continue

            if isinstance(task_result, list):
                table_results[table_name] = task_result
            else:
                table_results[table_name] = []

        return table_results

    def _sort_table_results(
        self,
        table_results: Dict[str, List[Any]],
        recognizer_settings: IntentRecognizerSettings,
    ) -> List[Any]:
        """按映射优先级展开并按相似度降序排序"""
        sorted_results: List[Any] = []

        for table_name in recognizer_settings.database_mapping.keys():
            sorted_results.extend(table_results.get(table_name, []))

        for table_name, table_items in table_results.items():
            if table_name not in recognizer_settings.database_mapping:
                sorted_results.extend(table_items)

        sorted_results.sort(key=self._safe_similarity, reverse=True)
        return sorted_results

    @staticmethod
    def _safe_similarity(result: Any) -> float:
        value = getattr(result, "total_similarity", 0.0)
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    async def _intent_judgment(
        self,
        query: str,
        judge_function: Optional[JudgeFunction] = None,
        mapping_file: Optional[str] = None,
    ) -> IntentResult:
        """意图判断核心流程：配置加载 -> 查表 -> 排序 -> 识别"""
        logger.info("开始意图判断,query='%s...'", query[:50])

        try:
            recognizer_settings = self._load_intent_recognizer_settings(
                mapping_file=mapping_file,
            )
            table_results = await self._query_table_results(
                query=query,
                recognizer_settings=recognizer_settings,
            )
            sorted_results = self._sort_table_results(
                table_results=table_results,
                recognizer_settings=recognizer_settings,
            )

            return self._build_intent_result(
                query=query,
                sorted_results=sorted_results,
                recognizer_settings=recognizer_settings,
                judge_function=judge_function,
            )

        except Exception as e:
            logger.error(f"意图判断异常: {str(e)}", exc_info=True)
            return IntentResult(
                type=settings.intent.default_type,
                query=query,
                results=[],
                similarity=0.0,
                database="",
            )

    def _build_intent_result(
        self,
        query: str,
        sorted_results: List[Any],
        recognizer_settings: IntentRecognizerSettings,
        judge_function: Optional[JudgeFunction] = None,
    ) -> IntentResult:
        """根据排序结果构建统一的意图结果"""
        recognized = recognize_intent_from_results(
            query=query,
            all_results=sorted_results,
            database_mapping=recognizer_settings.database_mapping,
            default_type=recognizer_settings.default_type,
            similarity_threshold=recognizer_settings.similarity_threshold,
            top_k=recognizer_settings.top_k,
            judge_function=judge_function,
        )

        logger.info(
            "最高相似度=%.4f, 知识库=%s",
            recognized.similarity,
            recognized.database,
        )

        top_results = [
            QueryResult(
                question=item.question,
                similarity=self._safe_similarity(item),
            )
            for item in recognized.database_results
        ]

        logger.info(
            "意图判断完成: type=%s, 知识库=%s, 相似度=%.4f, 返回结果数=%s",
            recognized.intent_type,
            recognized.database,
            recognized.similarity,
            len(top_results),
        )

        return IntentResult(
            type=recognized.intent_type,
            query=query,
            results=top_results,
            similarity=recognized.similarity,
            database=recognized.database,
        )
