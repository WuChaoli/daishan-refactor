"""
Dify SDK 异常类

定义了 SDK 中使用的所有异常类型,提供清晰的错误分类和处理。
"""

from typing import Any, Dict, Optional


class DifyError(Exception):
    """
    Dify SDK 基础异常类

    所有 Dify SDK 异常的基类,可用于捕获所有 SDK 相关的异常。

    Attributes:
        message: 错误消息
    """

    def __init__(self, message: str):
        """
        初始化异常

        Args:
            message: 错误消息
        """
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


class DifyAPIError(DifyError):
    """
    Dify API 错误

    当 Dify API 返回错误响应 (4xx, 5xx) 时抛出此异常。

    Attributes:
        message: 错误消息
        status_code: HTTP 状态码
        response: API 响应内容 (如果可解析为 JSON)
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化 API 错误

        Args:
            message: 错误消息
            status_code: HTTP 状态码 (如 400, 401, 404, 500 等)
            response: API 响应内容 (已解析的 JSON 字典)
        """
        super().__init__(message)
        self.status_code = status_code
        self.response = response

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class DifyConnectionError(DifyError):
    """
    网络连接错误

    当网络请求失败 (DNS 解析失败、连接超时、连接被拒绝等) 时抛出此异常。
    SDK 会自动重试 3 次,如果仍然失败则抛出此异常。

    Attributes:
        message: 错误消息
        original_error: 原始异常对象 (requests.RequestException)
    """

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        """
        初始化连接错误

        Args:
            message: 错误消息
            original_error: 原始异常对象 (来自 requests 库)
        """
        super().__init__(message)
        self.original_error = original_error

    def __str__(self) -> str:
        base_msg = f"连接错误: {self.message}"
        if self.original_error:
            base_msg += f" (原因: {type(self.original_error).__name__})"
        return base_msg


class DifyValidationError(DifyError):
    """
    参数验证错误

    当传递给 SDK 方法的参数不符合要求时抛出此异常。
    例如: 缺少必需参数、参数类型错误、参数值无效等。

    Attributes:
        message: 错误消息
        field: 出错的字段名 (可选)
    """

    def __init__(self, message: str, field: Optional[str] = None):
        """
        初始化验证错误

        Args:
            message: 错误消息
            field: 出错的字段名
        """
        super().__init__(message)
        self.field = field

    def __str__(self) -> str:
        if self.field:
            return f"参数错误 ({self.field}): {self.message}"
        return f"参数错误: {self.message}"
