"""
RagflowClient - RAGFlow 服务客户端适配器
负责与 RAGFlow 服务的交互,包括多知识库查询、结果解析和错误处理

使用根目录的 ragflow_sdk 作为底层实现
"""

import asyncio
from dataclasses import dataclass
from typing import Dict, List

from src.utils.log_manager_import import marker, trace
from src.config.settings import IntentConfig, RAGFlowConfig
from ragflow_sdk import RAGFlowClient
from ragflow_sdk.models import RetrievalRequest


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

        # 使用根目录的 ragflow_sdk RAGFlowClient
        self.client = RAGFlowClient(
            api_url=ragflow_config.base_url,
            api_key=ragflow_config.api_key,
            timeout=ragflow_config.timeout,
            max_retries=ragflow_config.max_retries,
            verify_ssl=True,
        )

        # 获取知识库列表
        self.datasets = self._get_datasets()
        self.dataset_map = {ds.name: ds for ds in self.datasets}

        marker(
            "ragflow.init",
            {
                "dataset_count": len(self.datasets),
                "names": list(self.dataset_map.keys()),
                "vector_similarity_weight": self._get_effective_vector_similarity_weight(),
            },
        )

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
        """获取知识库对象列表"""
        try:
            all_datasets = self.client.list_datasets(page=1, page_size=100)
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

    @trace
    async def query_all_databases(self, query: str) -> List[RetrievalResult]:
        """
        查询所有知识库并返回合并后的结果

        Args:
            query: 用户查询文本

        Returns:
            按相似度降序排序的检索结果列表
        """
        marker("ragflow.query_all.start", {"query_preview": query[:50], "query_len": len(query)})
        database_count = len(self.ragflow_config.database_mapping.keys())
        marker("ragflow.query_all.parallel_start", {"database_count": database_count, "query_len": len(query)})

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

        marker("ragflow.query_all.complete", {"result_count": len(all_results), "exception_count": exception_count})

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

    @trace
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

        # 检查知识库是否存在
        if database not in self.dataset_map:
            marker("ragflow.query_single.not_found", {"database": database}, level="WARNING")
            return []

        dataset = self.dataset_map[database]

        try:
            # 使用超时控制
            results = await asyncio.wait_for(
                self._query_with_sdk(query, dataset), timeout=5.0
            )

            marker("单库查询完成", {"database": database, "result_count": len(results)})
            return results

        except asyncio.TimeoutError:
            marker("单库查询超时", {"database": database, "timeout": 5}, level="WARNING")
            return []

        except Exception as e:
            marker("单库查询失败", {"database": database, "error": str(e)}, level="ERROR")
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
        marker("SDK检索返回", {"database": dataset.name, "chunk_count": chunk_count})

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
            top_k=1024,
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
        测试 RAGFlow 服务连接状态

        Returns:
            连接是否成功
        """
        try:
            datasets = self.client.list_datasets(page=1, page_size=1)
            marker("RAGFlow连接测试成功", {})
            return True
        except Exception as e:
            marker("RAGFlow连接测试失败", {"error": str(e)}, level="ERROR")
            return False
