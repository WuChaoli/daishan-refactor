"""BaseIntentService - 意图识别流程抽象基类"""

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Union

from log_decorator import logger
from src.config.settings import settings
from src.utils.ragflow_client import RagflowClient


@dataclass
class IntentRecognitionResult:
    """通用意图识别结果"""

    query: str
    intent_type: int
    database: str
    similarity: float
    database_results: List[Any]


@dataclass
class IntentRecognizerSettings:
    """意图识别参数配置"""

    database_mapping: Mapping[str, Any]
    similarity_threshold: float
    top_k: int
    default_type: int


DatabaseResultsDict = Dict[str, List[Any]]
JudgeFunction = Callable[[DatabaseResultsDict, IntentRecognizerSettings], Optional[Any]]


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

    @staticmethod
    def _default_mapping_file_path() -> Path:
        """获取默认映射文件路径"""
        return Path(__file__).resolve().parents[2] / "services" / "intent_mapping.example.json"

    @classmethod
    def _load_intent_recognizer_settings_from_json(
        cls,
        config_file: Optional[Union[str, Path]] = None,
    ) -> IntentRecognizerSettings:
        """从 JSON 文件加载意图识别设置"""
        config_path = Path(config_file) if config_file else cls._default_mapping_file_path()

        with open(config_path, "r", encoding="utf-8") as fp:
            payload = json.load(fp) or {}

        if not isinstance(payload, dict):
            raise ValueError("intent recognizer json 根节点必须是对象")

        database_mapping = payload.get("database_mapping", payload)
        if not isinstance(database_mapping, dict):
            raise ValueError("database_mapping 必须是对象")

        similarity_threshold = payload.get(
            "similarity_threshold",
            settings.intent.similarity_threshold,
        )
        top_k = payload.get(
            "top_k",
            payload.get("top_k_per_database", settings.intent.top_k_per_database),
        )
        default_type = payload.get("default_type", settings.intent.default_type)

        return IntentRecognizerSettings(
            database_mapping=database_mapping,
            similarity_threshold=float(similarity_threshold),
            top_k=int(top_k),
            default_type=int(default_type),
        )

    @staticmethod
    def _default_judge_function(
        table_results: DatabaseResultsDict,
        recognizer_settings: IntentRecognizerSettings,
    ) -> Optional[Any]:
        """默认判断逻辑：将各表结果展开后按相似度排序，取最高且>=阈值的候选"""
        flattened_results: List[Any] = []
        for table_name in recognizer_settings.database_mapping.keys():
            flattened_results.extend(table_results.get(table_name, []))

        for table_name, table_items in table_results.items():
            if table_name not in recognizer_settings.database_mapping:
                flattened_results.extend(table_items)

        if not flattened_results:
            return None

        flattened_results.sort(key=BaseIntentService._safe_similarity, reverse=True)
        candidate = flattened_results[0]
        if (
            BaseIntentService._safe_similarity(candidate)
            >= recognizer_settings.similarity_threshold
        ):
            return candidate
        return None

    @classmethod
    def _flatten_table_results(
        cls,
        table_results: DatabaseResultsDict,
        recognizer_settings: IntentRecognizerSettings,
    ) -> List[Any]:
        """按映射配置顺序展开各表结果，并按相似度降序"""
        flattened_results: List[Any] = []

        for table_name in recognizer_settings.database_mapping.keys():
            flattened_results.extend(table_results.get(table_name, []))

        for table_name, table_items in table_results.items():
            if table_name not in recognizer_settings.database_mapping:
                flattened_results.extend(table_items)

        flattened_results.sort(key=cls._safe_similarity, reverse=True)
        return flattened_results

    @classmethod
    def _build_intent_result_from_table_results(
        cls,
        query: str,
        table_results: DatabaseResultsDict,
        recognizer_settings: IntentRecognizerSettings,
        judge_function: Optional[JudgeFunction] = None,
    ) -> IntentRecognitionResult:
        """基于按表分组的结果，构建最终意图识别结果"""
        flattened_results = cls._flatten_table_results(table_results, recognizer_settings)
        if not flattened_results:
            return IntentRecognitionResult(
                query=query,
                intent_type=recognizer_settings.default_type,
                database="",
                similarity=0.0,
                database_results=[],
            )

        decide = judge_function or cls._default_judge_function
        judged_result = decide(table_results, recognizer_settings)
        best_result = judged_result or flattened_results[0]

        best_database = getattr(best_result, "database", "") or ""
        best_similarity = cls._safe_similarity(best_result)
        database_results = table_results.get(best_database, [])[: recognizer_settings.top_k]

        intent_type = cls._normalize_intent_type(
            recognizer_settings.database_mapping.get(
                best_database,
                recognizer_settings.default_type,
            ),
            recognizer_settings.default_type,
        )
        if judge_function is None and best_similarity < recognizer_settings.similarity_threshold:
            intent_type = recognizer_settings.default_type

        return IntentRecognitionResult(
            query=query,
            intent_type=intent_type,
            database=best_database,
            similarity=best_similarity,
            database_results=database_results,
        )

    @staticmethod
    def _normalize_intent_type(value: Any, default_type: int) -> int:
        """兼容意图映射值：支持 int 或 str（可转 int）"""
        if isinstance(value, bool):
            return int(value)

        if isinstance(value, int):
            return value

        if isinstance(value, str):
            text = value.strip()
            if text == "":
                return default_type
            try:
                return int(text)
            except ValueError:
                return default_type

        return default_type

    @classmethod
    def _recognize_intent_from_results(
        cls,
        query: str,
        all_results: Sequence[Any],
        database_mapping: Mapping[str, Any],
        default_type: int,
        similarity_threshold: float,
        top_k: int,
        judge_function: Optional[JudgeFunction] = None,
    ) -> IntentRecognitionResult:
        """通用意图识别入口（基于检索结果）"""
        recognizer_settings = IntentRecognizerSettings(
            database_mapping=database_mapping,
            similarity_threshold=similarity_threshold,
            top_k=top_k,
            default_type=default_type,
        )
        if top_k <= 0:
            raise ValueError(f"top_k must be positive, got {top_k}")

        table_results: DatabaseResultsDict = {}
        for item in all_results:
            table_name = getattr(item, "database", "") or ""
            table_results.setdefault(table_name, []).append(item)

        return cls._build_intent_result_from_table_results(
            query=query,
            table_results=table_results,
            recognizer_settings=recognizer_settings,
            judge_function=judge_function,
        )

    def __init__(self, ragflow_client: RagflowClient):
        self.ragflow_client = ragflow_client

    async def process_query(self, text_input: str, user_id: str) -> dict:
        """模板方法：配置加载 -> 查表 -> 排序 -> 后处理"""
        try:
            recognizer_settings = self._load_process_settings()
            table_results = await self._query_process_table_results(
                text_input,
                recognizer_settings,
            )
            sorted_results = self._sort_process_table_results(
                table_results,
                recognizer_settings,
            )
            judge_function = self._get_process_judge_function()
            intent_result = self._build_intent_result(
                query=text_input,
                sorted_results=sorted_results,
                recognizer_settings=recognizer_settings,
                judge_function=judge_function,
            )
            return await self._post_process_result(intent_result)
        except Exception as e:
            logger.error(f"处理查询异常: {str(e)}", exc_info=True)
            return self._build_process_error_result(e)

    @abstractmethod
    def _load_process_settings(self) -> IntentRecognizerSettings:
        """步骤1：加载意图识别配置"""

    @abstractmethod
    async def _query_process_table_results(
        self,
        text_input: str,
        recognizer_settings: IntentRecognizerSettings,
    ) -> Dict[str, List[Any]]:
        """步骤2：查询表结果"""

    @abstractmethod
    def _sort_process_table_results(
        self,
        table_results: Dict[str, List[Any]],
        recognizer_settings: IntentRecognizerSettings,
    ) -> List[Any]:
        """步骤3：排序表结果"""

    @abstractmethod
    async def _post_process_result(self, intent_result: IntentResult) -> dict:
        """步骤4：后处理并返回结果"""

    def _get_process_judge_function(self) -> Optional[JudgeFunction]:
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
        return self._load_intent_recognizer_settings_from_json(config_file=mapping_file)

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

    def _build_intent_result(
        self,
        query: str,
        sorted_results: List[Any],
        recognizer_settings: IntentRecognizerSettings,
        judge_function: Optional[JudgeFunction] = None,
    ) -> IntentResult:
        """根据排序结果构建统一的意图结果"""
        recognized = self._recognize_intent_from_results(
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
