"""
RagflowClient - RAGFlow 服务客户端适配器
负责与 RAGFlow 服务的交互,包括多知识库查询、结果解析和错误处理

使用根目录的 ragflow_sdk 作为底层实现
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, TypeVar

from rag_stream.utils.log_manager_import import marker, trace
from rag_stream.config.settings import IntentConfig, RAGFlowConfig
from ragflow_sdk import RAGFlowClient
from ragflow_sdk.models import RetrievalRequest

T = TypeVar("T")


def _build_result_summary_item(result: Any) -> dict[str, Any]:
    question = str(getattr(result, "question", "") or "").strip()
    return {
        "question": question,
        "similarity": float(getattr(result, "total_similarity", 0.0) or 0.0),
    }


def _build_result_summary_list(results: list[Any], limit: int = 3) -> list[dict[str, Any]]:
    summary_items: list[dict[str, Any]] = []
    for item in results[: max(int(limit), 0)]:
        summary_items.append(_build_result_summary_item(item))
    return summary_items


def with_retry(config: RAGFlowConfig, operation_name: str = "operation"):
    """
    重试装饰器，使用指数退避策略

    Args:
        config: RAGFlow 配置，包含重试参数
        operation_name: 操作名称，用于日志记录
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    is_last_attempt = attempt == config.max_retries

                    if is_last_attempt:
                        break

                    # 计算退避延迟
                    delay = min(
                        config.retry_delay * (config.retry_backoff_factor ** attempt),
                        config.retry_max_delay
                    )

                    marker(
                        f"ragflow.retry.{operation_name}",
                        {
                            "attempt": attempt + 1,
                            "max_retries": config.max_retries,
                            "delay": delay,
                            "error": str(e),
                        },
                        level="WARNING",
                    )

                    time.sleep(delay)

            # 所有重试都失败了
            raise last_exception

        return wrapper
    return decorator


async def with_retry_async(config: RAGFlowConfig, operation_name: str = "operation"):
    """
    异步重试装饰器，使用指数退避策略

    Args:
        config: RAGFlow 配置，包含重试参数
        operation_name: 操作名称，用于日志记录
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    is_last_attempt = attempt == config.max_retries

                    if is_last_attempt:
                        break

                    # 计算退避延迟
                    delay = min(
                        config.retry_delay * (config.retry_backoff_factor ** attempt),
                        config.retry_max_delay
                    )

                    marker(
                        f"ragflow.retry.{operation_name}",
                        {
                            "attempt": attempt + 1,
                            "max_retries": config.max_retries,
                            "delay": delay,
                            "error": str(e),
                        },
                        level="WARNING",
                    )

                    await asyncio.sleep(delay)

            # 所有重试都失败了
            raise last_exception

        return wrapper
    return decorator


@dataclass
class RetrievalResult:
    """RAGFlow 检索结果"""

    database: str  # 知识库名称
    question: str  # 匹配的问题原文
    total_similarity: float  # 总相似度
    keyword_similarity: float  # 关键词相似度
    vector_similarity: float  # 向量相似度


class RagflowClient:
    """RAGFlow 客户端适配器"""

    def __init__(
        self,
        ragflow_config: RAGFlowConfig,
        intent_config: IntentConfig,
    ):
        """
        初始化 RAGFlow 客户端

        Args:
            ragflow_config: RAGFlow 配置
            intent_config: 意图判断配置
        """
        self.ragflow_config = ragflow_config
        self.intent_config = intent_config
        self.single_query_timeout = float(ragflow_config.query_timeout)

        # 使用根目录的 ragflow_sdk RAGFlowClient
        self.client = RAGFlowClient(
            api_url=ragflow_config.base_url,
            api_key=ragflow_config.api_key,
            timeout=ragflow_config.timeout,
            max_retries=ragflow_config.max_retries,
            verify_ssl=True,
        )
        self._service_available = True

        # Lazy-load datasets to avoid blocking application startup.
        self.datasets: List = []
        self.dataset_map: Dict[str, object] = {}

        marker(
            "ragflow.init",
            {
                "dataset_count": len(self.datasets),
                "names": list(self.dataset_map.keys()),
                "vector_similarity_weight": self._get_effective_vector_similarity_weight(),
                "dataset_load_mode": "lazy",
            },
        )

    def set_service_available(self, available: bool) -> None:
        self._service_available = bool(available)

    def _ensure_datasets_loaded(self) -> None:
        """确保数据集已加载（带重试机制）"""
        if not self._service_available:
            return
        if self.dataset_map:
            return

        try:
            marker("ragflow.datasets.loading", {"max_retries": self.ragflow_config.max_retries})
            self.datasets = self._get_datasets()
            self.dataset_map = {ds.name: ds for ds in self.datasets}
            marker(
                "ragflow.datasets.loaded",
                {"count": len(self.datasets), "names": list(self.dataset_map.keys())},
            )
        except Exception as error:
            marker(
                "ragflow.datasets.lazy_load_failed",
                {"error": str(error)},
                level="WARNING",
            )
            self.datasets = []
            self.dataset_map = {}

    def _get_effective_vector_similarity_weight(self) -> float:
        """
        获取生效的向量权重配置。

        规则：
        - 若 intent 配置了 vector_similarity_weight，则使用 intent 值
        - 否则继承 ragflow 的基础配置值
        """
        if self.intent_config.vector_similarity_weight is not None:
            return float(self.intent_config.vector_similarity_weight)
        return float(self.ragflow_config.vector_similarity_weight)

    def _get_datasets(self) -> List:
        """获取知识库对象列表（带重试机制）"""
        @with_retry(self.ragflow_config, "list_datasets")
        def _fetch():
            # 使用更小的 page_size 和更短的超时时间
            return self.client.list_datasets(
                page=1,
                page_size=self.ragflow_config.list_datasets_page_size
            )

        try:
            marker("ragflow.datasets.fetch_start", {
                "page_size": self.ragflow_config.list_datasets_page_size,
                "max_retries": self.ragflow_config.max_retries,
            })

            all_datasets = _fetch()
            configured_databases = list(self.ragflow_config.database_mapping.keys())
            marker("ragflow.datasets.listed", {"configured_count": len(configured_databases)})

            found_datasets = []
            found_names = []

            for dataset in all_datasets.get("items", []):
                if dataset.name in configured_databases:
                    found_datasets.append(dataset)
                    found_names.append(dataset.name)

            # 检查是否找到所有配置的知识库
            missing_names = [
                name for name in configured_databases if name not in found_names
            ]
            if missing_names:
                marker("ragflow.datasets.missing", {"names": ', '.join(missing_names)}, level="WARNING")

            marker("ragflow.datasets.mapped", {"found_count": len(found_datasets), "missing_count": len(missing_names)})
            return found_datasets

        except Exception as e:
            marker("ragflow.datasets.error", {"error": str(e)}, level="ERROR")
            raise

    async def query_all_databases(self, query: str) -> List[RetrievalResult]:
        """
        查询所有知识库并返回合并后的结果

        Args:
            query: 用户查询文本

        Returns:
            按相似度降序排序的检索结果列表
        """
        marker("ragflow.query_all.start", {"query_len": len(query)})
        database_count = len(self.ragflow_config.database_mapping.keys())

        # 并发查询所有知识库
        tasks = [
            self.query_single_database(query, db_name)
            for db_name in self.ragflow_config.database_mapping.keys()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并所有结果
        all_results = []
        exception_count = 0
        for result in results:
            if isinstance(result, Exception):
                marker("ragflow.query_all.exception", {"error": str(result)}, level="ERROR")
                exception_count += 1
                continue
            if isinstance(result, list):
                all_results.extend(result)

        marker(
            "ragflow.query_all.complete",
            {
                "query_len": len(query),
                "database_count": database_count,
                "result_count": len(all_results),
                "exception_count": exception_count,
                "top_results": _build_result_summary_list(all_results),
            },
        )

        # 按相似度降序排序
        all_results.sort(key=lambda x: x.total_similarity, reverse=True)
        instruct_results = result[0]
        if isinstance(instruct_results, list):
            if len(instruct_results) > 0:
                instruct_results[0].sort(key=lambda x: x.total_similarity, reverse=True)
        else:
            instruct_results = []

        return all_results, instruct_results
        # return all_results

    async def query_single_database(
        self, query: str, database: str
    ) -> List[RetrievalResult]:
        """
        查询单个知识库

        Args:
            query: 用户查询文本
            database: 知识库名称

        Returns:
            检索结果列表
        """
        marker("ragflow.query_single.start", {"database": database, "query_len": len(query)})
        if not self._service_available:
            marker(
                "ragflow.query_single.degraded_skip",
                {"database": database},
                level="WARNING",
            )
            return []
        self._ensure_datasets_loaded()

        # 检查知识库是否存在
        if database not in self.dataset_map:
            marker("ragflow.query_single.not_found", {"database": database}, level="WARNING")
            return []

        dataset = self.dataset_map[database]

        try:
            # 使用超时控制
            results = await asyncio.wait_for(
                self._query_with_sdk(query, dataset),
                timeout=self.single_query_timeout,
            )

            marker(
                "ragflow.query_single.complete",
                {
                    "database": database,
                    "query_len": len(query),
                    "chunk_count": len(results),
                    "top_question": str(results[0].question or "") if results else "",
                    "top_similarity": float(results[0].total_similarity) if results else 0.0,
                },
            )
            return results

        except asyncio.TimeoutError:
            marker(
                "ragflow.query_single.timeout",
                {"database": database, "query_len": len(query), "timeout": self.single_query_timeout},
                level="WARNING",
            )
            return []

        except Exception as e:
            marker(
                "ragflow.query_single.failed",
                {"database": database, "query_len": len(query), "error": str(e)},
                level="ERROR",
            )
            return []

    async def _query_with_sdk(self, query: str, dataset) -> List[RetrievalResult]:
        """
        使用 RAGFlow SDK 执行查询

        Args:
            query: 查询文本
            dataset: 知识库对象

        Returns:
            检索结果列表
        """
        # 在线程池中执行同步的 SDK 调用
        loop = asyncio.get_event_loop()

        retrieval = self._build_retrieval_request(query=query, dataset_id=dataset.id)

        chunks = await loop.run_in_executor(
            None, lambda: self.client.retrieve(retrieval)
        )
        chunk_count = len(chunks) if chunks else 0

        results = []
        if chunks:
            for chunk in chunks:
                result = RetrievalResult(
                    database=dataset.name,
                    question=chunk.content,
                    total_similarity=self._parse_similarity(chunk, "total"),
                    keyword_similarity=self._parse_similarity(chunk, "keyword"),
                    vector_similarity=self._parse_similarity(chunk, "vector"),
                )
                results.append(result)

        marker(
            "ragflow.query_sdk.complete",
            {
                "database": dataset.name,
                "query_len": len(query),
                "chunk_count": chunk_count,
                "top_question": str(results[0].question or "") if results else "",
                "top_similarity": float(results[0].total_similarity) if results else 0.0,
            },
        )
        return results

    def _build_retrieval_request(self, query: str, dataset_id: str) -> RetrievalRequest:
        """构建检索请求参数。"""
        return RetrievalRequest(
            question=query,
            dataset_ids=[dataset_id],
            page=1,
            page_size=self.intent_config.top_k_per_database,
            similarity_threshold=0.0,  # 不过滤,获取所有结果
            vector_similarity_weight=self._get_effective_vector_similarity_weight(),
            top_k=self.ragflow_config.retrieval_top_k,
        )

    def _parse_similarity(self, chunk, similarity_type: str) -> float:
        """
        解析 RAGFlow 返回的相似度分数

        Args:
            chunk: RAGFlow chunk 对象
            similarity_type: 相似度类型 ('total', 'keyword', 'vector')

        Returns:
            相似度分数
        """
        # 总相似度优先级: similarity > score
        if similarity_type == "total":
            if hasattr(chunk, "similarity"):
                return float(chunk.similarity)
            elif hasattr(chunk, "score"):
                return float(chunk.score)

        # 关键词相似度
        elif similarity_type == "keyword":
            if hasattr(chunk, "term_similarity"):
                return float(chunk.term_similarity)

        # 向量相似度
        elif similarity_type == "vector":
            if hasattr(chunk, "vector_similarity"):
                return float(chunk.vector_similarity)

        return 0.0

    def test_connection(self) -> bool:
        """
        测试 RAGFlow 服务连接状态（带重试机制）

        Returns:
            连接是否成功
        """
        @with_retry(self.ragflow_config, "test_connection")
        def _test():
            return self.client.list_datasets(page=1, page_size=1)

        try:
            datasets = _test()
            marker("ragflow.connection_test.success", {"datasets_found": len(datasets.get("items", []))})
            self._service_available = True
            return True
        except Exception as e:
            marker("ragflow.connection_test.failed", {"error": str(e)}, level="ERROR")
            self._service_available = False
            return False
