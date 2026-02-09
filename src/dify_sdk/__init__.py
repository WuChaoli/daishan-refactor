"""
Dify 工作流 API SDK

提供简洁的 Pythonic API 接口,用于与 Dify 工作流服务交互。

示例:
    >>> import os
    >>> os.environ['DIFY_API_KEY'] = 'your-api-key'
    >>>
    >>> from dify_sdk import DifyClient
    >>>
    >>> # 创建客户端
    >>> client = DifyClient()
    >>>
    >>> # 同步执行工作流
    >>> response = client.run_workflow(
    ...     inputs={'query': '岱山园区有哪些企业?'},
    ...     user='user-123'
    ... )
    >>> print(response.result)
    >>>
    >>> # 流式执行工作流
    >>> for event in client.run_workflow_streaming(
    ...     inputs={'query': '分析安全风险'},
    ...     user='user-123'
    ... ):
    ...     if event.event_type == 'workflow_finished':
    ...         print(f"完成: {event.data.status}")
"""

__version__ = "1.0.0"
__author__ = "Dify SDK Team"

# 导出主客户端类
from .client import DifyClient
# 导出配置类
from .core.config import Config
# 导出异常类
from .core.exceptions import (DifyAPIError, DifyConnectionError, DifyError,
                              DifyValidationError)
# 导出 HTTP 客户端
from .http import HTTPClient
# 导出数据模型
from .models import (FileUploadResponse, TaskStatus, TaskStopResponse,
                     WorkflowRunRequest, WorkflowRunResponse,
                     WorkflowStreamEvent, WorkflowStreamEventData)
# 导出流式解析器
from .parsers import StreamingParser, DaishanStreamingParser

__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    # 主客户端类
    "DifyClient",
    # 异常类
    "DifyError",
    "DifyAPIError",
    "DifyConnectionError",
    "DifyValidationError",
    # 数据模型
    "WorkflowRunRequest",
    "WorkflowRunResponse",
    "TaskStatus",
    "TaskStopResponse",
    "WorkflowStreamEvent",
    "WorkflowStreamEventData",
    "FileUploadResponse",
    # 核心类
    "Config",
    "HTTPClient",
    "StreamingParser",
    "DaishanStreamingParser",
]
