"""
RAGFlow SDK 异常类模块

设计原则：
- 清晰的异常层次结构
- 详细的错误信息
- 友好的错误提示
- 包含上下文信息方便调试
"""

from typing import Any, Dict, Optional


class RAGFlowSDKError(Exception):
    """
    RAGFlow SDK 基础异常类

    所有 SDK 异常的父类，提供统一的错误信息格式
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        初始化异常

        Args:
            message: 错误消息（用户友好的描述）
            error_code: 错误代码（用于程序化处理）
            details: 额外的错误详情
            original_error: 原始异常对象
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.original_error = original_error

        # 构建完整的错误信息
        full_message = message
        if error_code:
            full_message = f"[{error_code}] {message}"

        super().__init__(full_message)

    def __str__(self) -> str:
        """提供格式化的错误信息"""
        lines = [str(self.args[0])]

        # 添加详情
        if self.details:
            lines.append("\n详细信息:")
            for key, value in self.details.items():
                # 限制值的长度，避免输出过长
                value_str = str(value)
                if len(value_str) > 200:
                    value_str = value_str[:200] + "..."
                lines.append(f"  • {key}: {value_str}")

        # 添加原始异常信息
        if self.original_error:
            lines.append(
                f"\n原始错误: {type(self.original_error).__name__}: {self.original_error}"
            )

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（用于日志记录）"""
        return {
            "error": self.message,  # 向后兼容：提供 "error" 键
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "original_error": str(self.original_error) if self.original_error else None,
        }


class ConfigurationError(RAGFlowSDKError):
    """配置错误"""

    def __init__(self, message: str, **kwargs):
        kwargs.setdefault("error_code", "CONFIG_ERROR")
        super().__init__(message, **kwargs)


class HTTPError(RAGFlowSDKError):
    """
    HTTP 请求错误

    包含详细的 HTTP 响应信息
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        request_url: Optional[str] = None,
        request_method: Optional[str] = None,
        **kwargs,
    ):
        """
        初始化 HTTP 错误

        Args:
            message: 错误消息
            status_code: HTTP 状态码
            response_body: 响应体内容
            request_url: 请求 URL
            request_method: 请求方法
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})

        # 添加 HTTP 特定的详情
        if status_code is not None:
            details["status_code"] = status_code
        if request_url:
            details["url"] = request_url
        if request_method:
            details["method"] = request_method
        if response_body and len(response_body) < 1000:
            details["response_preview"] = response_body

        kwargs["details"] = details
        kwargs.setdefault(
            "error_code", f"HTTP_{status_code}" if status_code else "HTTP_ERROR"
        )

        super().__init__(message, **kwargs)

        self.status_code = status_code
        self.response_body = response_body
        self.request_url = request_url
        self.request_method = request_method

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（包含 HTTP 特定字段）"""
        result = super().to_dict()
        # 添加 HTTP 特定字段到顶层
        if self.status_code is not None:
            result["status_code"] = self.status_code
        if self.request_url:
            result["request_url"] = self.request_url
        if self.request_method:
            result["request_method"] = self.request_method
        return result


class ParseError(RAGFlowSDKError):
    """
    响应解析错误

    提供原始数据信息方便调试
    """

    def __init__(
        self,
        message: str,
        raw_data: Optional[Any] = None,
        expected_format: Optional[str] = None,
        **kwargs,
    ):
        """
        初始化解析错误

        Args:
            message: 错误消息
            raw_data: 原始数据
            expected_format: 期望的格式
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})

        if raw_data is not None:
            raw_str = str(raw_data)
            details["raw_data_preview"] = (
                raw_str[:500] if len(raw_str) > 500 else raw_str
            )

        if expected_format:
            details["expected_format"] = expected_format

        kwargs["details"] = details
        kwargs.setdefault("error_code", "PARSE_ERROR")

        super().__init__(message, **kwargs)

        self.raw_data = raw_data


class ValidationError(RAGFlowSDKError):
    """数据验证错误"""

    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        details = kwargs.get("details", {})
        if field:
            details["field"] = field
        kwargs["details"] = details
        kwargs.setdefault("error_code", "VALIDATION_ERROR")
        super().__init__(message, **kwargs)


class AuthenticationError(RAGFlowSDKError):
    """认证错误"""

    def __init__(self, message: str = "认证失败，请检查 API Key", **kwargs):
        kwargs.setdefault("error_code", "AUTH_ERROR")
        super().__init__(message, **kwargs)


class RateLimitError(RAGFlowSDKError):
    """请求频率限制错误"""

    def __init__(
        self,
        message: str = "请求过于频繁，请稍后重试",
        retry_after: Optional[int] = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if retry_after:
            details["retry_after_seconds"] = retry_after
        kwargs["details"] = details
        kwargs.setdefault("error_code", "RATE_LIMIT_ERROR")
        super().__init__(message, **kwargs)


class ResourceNotFoundError(RAGFlowSDKError):
    """资源未找到错误"""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        kwargs["details"] = details
        kwargs.setdefault("error_code", "NOT_FOUND")
        super().__init__(message, **kwargs)


class TimeoutError(RAGFlowSDKError):
    """请求超时错误"""

    def __init__(
        self, message: str = "请求超时", timeout: Optional[int] = None, **kwargs
    ):
        details = kwargs.get("details", {})
        if timeout:
            details["timeout_seconds"] = timeout
        kwargs["details"] = details
        kwargs.setdefault("error_code", "TIMEOUT_ERROR")
        super().__init__(message, **kwargs)
