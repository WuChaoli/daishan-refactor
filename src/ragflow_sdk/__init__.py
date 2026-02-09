"""
RAGFlow SDK - 通用 RAGFlow API 客户端库

特性：
- 高度模块化和可扩展
- 清晰的错误处理
- 类型安全
- 完整的文档
- 易于使用

基本用法：
    from ragflow_sdk import RAGFlowClient

    # 使用配置文件
    client = RAGFlowClient.from_config("config.yaml")

    # 或直接指定参数
    client = RAGFlowClient(
        api_url="http://localhost:80/v1",
        api_key="your-api-key"
    )

    # 使用客户端
    datasets = client.list_datasets()
"""

__version__ = "0.1.0"
__author__ = "RAGFlow SDK Team"

# 配置管理（独立使用）
from .config.manager import ConfigManager
# 核心客户端
from .core.client import RAGFlowClient
# 异常类
from .core.exceptions import (AuthenticationError, ConfigurationError,
                              HTTPError, ParseError, RAGFlowSDKError,
                              RateLimitError, ResourceNotFoundError,
                              TimeoutError, ValidationError)
# HTTP 客户端（独立使用）
from .http.client import HTTPClient
# 常用数据模型（便捷导入）
from .models import (Chat,  # 数据集模型; 文档模型; Chunk 模型; 聊天模型
                     ChatCompletionRequest, ChatCreate, ChatSession,
                     ChatUpdate, Chunk, ChunkCreate, ChunkUpdate, Dataset,
                     DatasetCreate, DatasetListParams, DatasetUpdate, Document,
                     DocumentCreate, DocumentListParams, DocumentUpdate,
                     RetrievalRequest)

__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    # 核心客户端
    "RAGFlowClient",
    # 异常类
    "RAGFlowSDKError",
    "ConfigurationError",
    "HTTPError",
    "ParseError",
    "ValidationError",
    "AuthenticationError",
    "RateLimitError",
    "ResourceNotFoundError",
    "TimeoutError",
    # 数据集模型
    "Dataset",
    "DatasetCreate",
    "DatasetUpdate",
    "DatasetListParams",
    # 文档模型
    "Document",
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentListParams",
    # Chunk 模型
    "Chunk",
    "ChunkCreate",
    "ChunkUpdate",
    "RetrievalRequest",
    # 聊天模型
    "Chat",
    "ChatCreate",
    "ChatUpdate",
    "ChatSession",
    "ChatCompletionRequest",
    # 独立模块
    "HTTPClient",
    "ConfigManager",
]
