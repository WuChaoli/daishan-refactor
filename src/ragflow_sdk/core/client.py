"""
RAGFlow 客户端主类

设计原则：
- 易用性：提供简洁直观的 API
- 通用性：支持所有 RAGFlow API 功能
- 可扩展：易于添加新功能
- 类型安全：完整的类型注解
- 错误处理：清晰的错误信息
"""

from typing import Any, Dict, List, Optional, Union

from ..config.manager import ConfigManager
from ..http.client import HTTPClient
from ..models import (Chat, ChatCompletionRequest, ChatCreate, ChatSession,
                      Chunk, ChunkCreate, ChunkUpdate, Dataset, DatasetCreate,
                      DatasetUpdate, Document, RetrievalRequest)
from ..parsers.ragflow import RAGFlowParser
from .exceptions import RAGFlowSDKError


class RAGFlowClient:
    """
    RAGFlow API 客户端

    这是 SDK 的主入口，提供所有 RAGFlow API 功能的访问

    特性：
    - 支持多种初始化方式（配置文件、环境变量、直接参数）
    - 自动认证和会话管理
    - 完整的错误处理
    - 链式 API 调用
    - 类型安全

    基本用法：
        # 使用配置文件
        client = RAGFlowClient.from_config("config.yaml")

        # 使用环境变量
        client = RAGFlowClient.from_env()

        # 直接指定参数
        client = RAGFlowClient(
            api_url="http://localhost:80/v1",
            api_key="your-api-key"
        )
    """

    def __init__(
        self,
        api_url: str,
        api_key: str,
        *,
        timeout: int = 30,
        max_retries: int = 3,
        verify_ssl: bool = True,
    ):
        """
        初始化 RAGFlow 客户端

        Args:
            api_url: API 基础 URL
            api_key: API 密钥
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            verify_ssl: 是否验证 SSL 证书
        """
        # 初始化 HTTP 客户端
        self.http = HTTPClient(
            base_url=api_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
            verify_ssl=verify_ssl,
        )

        # 初始化解析器
        self.parser = RAGFlowParser()

    @classmethod
    def from_config(cls, config_path: str) -> "RAGFlowClient":
        """
        从配置文件创建客户端

        Args:
            config_path: 配置文件路径

        Returns:
            RAGFlow 客户端实例

        Raises:
            ConfigurationError: 配置加载或验证失败时抛出
        """
        config = ConfigManager(config_path)
        config.validate()

        return cls(
            api_url=config.get_base_url(),
            api_key=config.get_api_key(),
            timeout=config.get_timeout(),
            max_retries=config.get_max_retries(),
            verify_ssl=config.get_verify_ssl(),
        )

    @classmethod
    def from_env(cls) -> "RAGFlowClient":
        """
        从环境变量创建客户端

        支持的环境变量：
        - RAGFLOW_BASE_URL: API 基础 URL
        - RAGFLOW_API_KEY: API 密钥
        - RAGFLOW_TIMEOUT: 超时时间
        - RAGFLOW_MAX_RETRIES: 最大重试次数
        - RAGFLOW_VERIFY_SSL: 是否验证 SSL

        Returns:
            RAGFlow 客户端实例

        Raises:
            ConfigurationError: 配置验证失败时抛出
        """
        config = ConfigManager()
        config.validate()

        return cls(
            api_url=config.get_base_url(),
            api_key=config.get_api_key(),
            timeout=config.get_timeout(),
            max_retries=config.get_max_retries(),
            verify_ssl=config.get_verify_ssl(),
        )

    # ==================== 数据集管理 ====================

    def create_dataset(self, dataset: DatasetCreate) -> Dataset:
        """
        创建数据集

        Args:
            dataset: 数据集创建请求

        Returns:
            创建的数据集

        Raises:
            RAGFlowSDKError: API 调用失败时抛出
        """
        response = self.http.post("/datasets", json=dataset.dict())
        return self.parser.parse_object(response, Dataset)

    def get_dataset(self, dataset_id: str) -> Dataset:
        """
        获取数据集详情

        Args:
            dataset_id: 数据集 ID

        Returns:
            数据集详情

        Raises:
            RAGFlowSDKError: API 调用失败时抛出
        """
        # 注意：RAGFlow 可能没有单独的获取详情接口，这里需要从列表中查找
        # 如果有独立的接口，应该使用 GET /datasets/{dataset_id}
        datasets = self.list_datasets(id=dataset_id)
        if datasets["items"]:
            return datasets["items"][0]
        raise RAGFlowSDKError(f"数据集不存在: {dataset_id}")

    def list_datasets(
        self,
        page: int = 1,
        page_size: int = 10,
        orderby: str = "create_time",
        desc: bool = True,
        name: Optional[str] = None,
        id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        列出数据集

        Args:
            page: 页码
            page_size: 每页数量
            orderby: 排序字段
            desc: 是否降序
            name: 数据集名称（模糊搜索）
            id: 数据集 ID（精确搜索）

        Returns:
            包含 items 和 total 的字典
        """
        params = {
            "page": page,
            "page_size": page_size,
            "orderby": orderby,
            "desc": desc,
        }
        if name:
            params["name"] = name
        if id:
            params["id"] = id

        response = self.http.get("/datasets", params=params)
        return self.parser.parse_paginated(response, Dataset)

    def update_dataset(self, dataset_id: str, dataset: DatasetUpdate) -> Dataset:
        """
        更新数据集

        Args:
            dataset_id: 数据集 ID
            dataset: 更新请求

        Returns:
            更新后的数据集

        Raises:
            RAGFlowSDKError: API 调用失败时抛出
        """
        # 只传递非 None 的字段
        update_data = {k: v for k, v in dataset.dict().items() if v is not None}
        response = self.http.put(f"/datasets/{dataset_id}", json=update_data)
        return self.parser.parse_object(response, Dataset)

    def delete_datasets(self, dataset_ids: Optional[List[str]] = None) -> bool:
        """
        删除数据集

        Args:
            dataset_ids: 数据集 ID 列表，为 None 时删除所有数据集

        Returns:
            是否成功

        Raises:
            RAGFlowSDKError: API 调用失败时抛出
        """
        json_data = {} if dataset_ids is None else {"ids": dataset_ids}
        response = self.http.delete("/datasets", json=json_data)
        self.parser.parse(response)
        return True

    # ==================== 文档管理 ====================

    def upload_document(
        self, dataset_id: str, file_path: str, name: Optional[str] = None
    ) -> Document:
        """
        上传文档

        Args:
            dataset_id: 数据集 ID
            file_path: 文件路径
            name: 文档名称（可选）

        Returns:
            上传的文档信息

        Raises:
            RAGFlowSDKError: API 调用失败时抛出
        """
        import os
        from pathlib import Path

        file_path = Path(file_path)
        if not file_path.exists():
            raise RAGFlowSDKError(f"文件不存在: {file_path}")

        # 准备文件和数据
        files = {"file": open(file_path, "rb")}
        data = {}
        if name:
            data["name"] = name

        try:
            response = self.http.post(
                f"/datasets/{dataset_id}/documents", data=data, files=files
            )
            return self.parser.parse_object(response, Document)
        finally:
            files["file"].close()

    def list_documents(
        self,
        dataset_id: str,
        page: int = 1,
        page_size: int = 10,
        orderby: str = "create_time",
        desc: bool = True,
        keywords: Optional[str] = None,
        id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        列出文档

        Args:
            dataset_id: 数据集 ID
            page: 页码
            page_size: 每页数量
            orderby: 排序字段
            desc: 是否降序
            keywords: 关键词搜索
            id: 文档 ID
            name: 文档名称

        Returns:
            包含 items 和 total 的字典
        """
        params = {
            "page": page,
            "page_size": page_size,
            "orderby": orderby,
            "desc": desc,
        }
        if keywords:
            params["keywords"] = keywords
        if id:
            params["id"] = id
        if name:
            params["name"] = name

        response = self.http.get(f"/datasets/{dataset_id}/documents", params=params)
        return self.parser.parse_paginated(response, Document)

    def delete_documents(
        self, dataset_id: str, document_ids: Optional[List[str]] = None
    ) -> bool:
        """
        删除文档

        Args:
            dataset_id: 数据集 ID
            document_ids: 文档 ID 列表，为 None 时删除所有文档

        Returns:
            是否成功

        Raises:
            RAGFlowSDKError: API 调用失败时抛出
        """
        json_data = {} if document_ids is None else {"ids": document_ids}
        response = self.http.delete(f"/datasets/{dataset_id}/documents", json=json_data)
        self.parser.parse(response)
        return True

    # ==================== Chunk 管理 ====================

    def create_chunk(self, dataset_id: str, chunk: ChunkCreate) -> Chunk:
        """
        创建 Chunk

        Args:
            dataset_id: 数据集 ID
            chunk: Chunk 创建请求

        Returns:
            创建的 Chunk

        Raises:
            RAGFlowSDKError: API 调用失败时抛出
        """
        response = self.http.post(f"/datasets/{dataset_id}/chunks", json=chunk.dict())
        return self.parser.parse_object(response, Chunk)

    def retrieve(self, retrieval: RetrievalRequest) -> List[Chunk]:
        """
        检索

        Args:
            retrieval: 检索请求

        Returns:
            检索到的 Chunk 列表

        Raises:
            RAGFlowSDKError: API 调用失败时抛出
        """
        payload = (
            retrieval.model_dump(exclude_none=True)
            if hasattr(retrieval, "model_dump")
            else retrieval.dict(exclude_none=True)
        )
        response = self.http.post("/retrieval", json=payload)
        return self.parser.parse_list(response, Chunk)

    # ==================== 聊天管理 ====================

    def create_chat(self, chat: ChatCreate) -> Chat:
        """
        创建聊天助手

        Args:
            chat: 聊天助手创建请求

        Returns:
            创建的聊天助手

        Raises:
            RAGFlowSDKError: API 调用失败时抛出
        """
        response = self.http.post("/chats", json=chat.dict())
        return self.parser.parse_object(response, Chat)

    def list_chats(
        self,
        page: int = 1,
        page_size: int = 10,
        orderby: str = "create_time",
        desc: bool = True,
        name: Optional[str] = None,
        id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        列出聊天助手

        Args:
            page: 页码
            page_size: 每页数量
            orderby: 排序字段
            desc: 是否降序
            name: 聊天助手名称
            id: 聊天助手 ID

        Returns:
            包含 items 和 total 的字典
        """
        params = {
            "page": page,
            "page_size": page_size,
            "orderby": orderby,
            "desc": desc,
        }
        if name:
            params["name"] = name
        if id:
            params["id"] = id

        response = self.http.get("/chats", params=params)
        return self.parser.parse_paginated(response, Chat)

    def delete_chats(self, chat_ids: Optional[List[str]] = None) -> bool:
        """
        删除聊天助手

        Args:
            chat_ids: 聊天助手 ID 列表，为 None 时删除所有

        Returns:
            是否成功

        Raises:
            RAGFlowSDKError: API 调用失败时抛出
        """
        json_data = {} if chat_ids is None else {"ids": chat_ids}
        response = self.http.delete("/chats", json=json_data)
        self.parser.parse(response)
        return True

    def chat_completion(
        self, chat_id: str, request: ChatCompletionRequest
    ) -> Dict[str, Any]:
        """
        聊天补全

        Args:
            chat_id: 聊天助手 ID
            request: 补全请求

        Returns:
            包含 answer 和 reference 的字典

        Raises:
            RAGFlowSDKError: API 调用失败时抛出
        """
        response = self.http.post(f"/chats/{chat_id}/completions", json=request.dict())
        return self.parser.parse_data(response)

    # ==================== 资源管理 ====================

    def close(self):
        """关闭客户端，释放资源"""
        if self.http:
            self.http.close()

    def __enter__(self):
        """支持上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时关闭客户端"""
        self.close()

    def __del__(self):
        """析构时关闭客户端"""
        self.close()
