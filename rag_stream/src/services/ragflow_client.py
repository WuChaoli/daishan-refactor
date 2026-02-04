"""
RagflowClient - RAGFlow 服务客户端适配器
负责与 RAGFlow 服务的交互,包括多知识库查询、结果解析和错误处理

使用根目录的 ragflow_sdk 作为底层实现
"""

import asyncio
from dataclasses import dataclass
from typing import Dict, List

from src.services.log_manager import LogManager
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
        log_manager: LogManager,
    ):
        """
        初始化 RAGFlow 客户端

        Args:
            ragflow_config: RAGFlow 配置
            intent_config: 意图判断配置
            log_manager: 日志管理器
        """
        self.ragflow_config = ragflow_config
        self.intent_config = intent_config
        self.log_manager = log_manager
        self.logger = log_manager.get_function_logger("ragflow_client")

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

        self.logger.info(
            f"RAGFlow 客户端初始化成功,已加载 {len(self.datasets)} 个知识库"
        )
        self.log_manager.log_info(
            f"RAGFlow 客户端初始化完成,知识库列表: {list(self.dataset_map.keys())}"
        )

    def _get_datasets(self) -> List:
        """获取知识库对象列表"""
        try:
            all_datasets = self.client.list_datasets(page=1, page_size=100)
            configured_databases = list(self.ragflow_config.database_mapping.keys())

            found_datasets = []
            found_names = []

            for dataset in all_datasets.get("items", []):
                if dataset.name in configured_databases:
                    self.logger.info(f"找到知识库 '{dataset.name}',ID: {dataset.id}")
                    found_datasets.append(dataset)
                    found_names.append(dataset.name)

            # 检查是否找到所有配置的知识库
            missing_names = [
                name for name in configured_databases if name not in found_names
            ]
            if missing_names:
                self.logger.warning(f"未找到以下知识库: {', '.join(missing_names)}")
                self.log_manager.log_error(f"配置的知识库不存在: {missing_names}")

            return found_datasets

        except Exception as e:
            self.logger.error(f"获取知识库列表失败: {str(e)}")
            self.log_manager.log_error(f"获取知识库列表失败: {str(e)}", exc_info=True)
            raise

    async def query_all_databases(self, query: str) -> List[RetrievalResult]:
        """
        查询所有知识库并返回合并后的结果

        Args:
            query: 用户查询文本

        Returns:
            按相似度降序排序的检索结果列表
        """
        self.logger.info(f"开始查询所有知识库,query='{query[:50]}...'")

        # 并发查询所有知识库
        tasks = [
            self.query_single_database(query, db_name)
            for db_name in self.ragflow_config.database_mapping.keys()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并所有结果
        all_results = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"查询异常: {str(result)}")
                continue
            if isinstance(result, list):
                all_results.extend(result)

        self.logger.info(f"查询完成,共获得 {len(all_results)} 条结果")

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
        self.logger.info(f"查询知识库: {database}")

        # 检查知识库是否存在
        if database not in self.dataset_map:
            self.logger.error(f"知识库 '{database}' 不存在")
            return []

        dataset = self.dataset_map[database]

        try:
            # 使用超时控制
            results = await asyncio.wait_for(
                self._query_with_sdk(query, dataset), timeout=5.0
            )

            self.logger.info(
                f"知识库 '{database}' 查询成功,返回 {len(results)} 条结果"
            )
            return results

        except asyncio.TimeoutError:
            self.logger.warning(f"知识库 '{database}' 查询超时 (5秒)")
            self.log_manager.log_function(
                "ragflow_client",
                "WARNING",
                f"查询超时",
                database=database,
                query=query[:50],
            )
            return []

        except Exception as e:
            self.logger.error(f"知识库 '{database}' 查询失败: {str(e)}")
            self.log_manager.log_function(
                "ragflow_client", "ERROR", f"查询失败", database=database, error=str(e)
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

        # 构建检索请求
        retrieval = RetrievalRequest(
            question=query,
            dataset_ids=[dataset.id],
            page=1,
            page_size=self.intent_config.top_k_per_database,
            similarity_threshold=0.0,  # 不过滤,获取所有结果
            top_k=1024,
        )

        chunks = await loop.run_in_executor(
            None, lambda: self.client.retrieve(retrieval)
        )

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
            self.logger.info(f"连接测试成功")
            return True
        except Exception as e:
            self.logger.error(f"连接测试失败: {str(e)}")
            return False
