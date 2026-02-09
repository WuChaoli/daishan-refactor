"""
通用 HTTP 客户端模块

设计原则：
- 完全解耦，可用于任何 HTTP API
- 支持会话管理和连接池
- 自动重试机制
- 详细的错误处理
- 灵活的配置选项
"""

import json
from typing import Any, Dict, Optional, Union
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException, Timeout
from urllib3.util.retry import Retry

from ..core.exceptions import HTTPError, TimeoutError


class HTTPClient:
    """
    通用 HTTP 客户端

    特性：
    - 自动会话管理和连接池复用
    - 智能重试策略（针对可重试的 HTTP 状态码）
    - 灵活的认证方式
    - 超时控制
    - 详细的错误信息和调试支持
    - 完全解耦，不依赖任何业务逻辑
    """

    def __init__(
        self,
        base_url: str,
        *,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_backoff_factor: float = 0.5,
        default_headers: Optional[Dict[str, str]] = None,
        verify_ssl: bool = True,
    ):
        """
        初始化 HTTP 客户端

        Args:
            base_url: API 基础 URL（例如：https://api.example.com/v1）
            api_key: API 密钥（用于 Authorization header）
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_backoff_factor: 重试退避因子
            default_headers: 默认请求头
            verify_ssl: 是否验证 SSL 证书
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.api_key = api_key
        self.verify_ssl = verify_ssl

        # 配置重试策略
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=retry_backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=[
                "HEAD",
                "GET",
                "POST",
                "PUT",
                "DELETE",
                "OPTIONS",
                "PATCH",
            ],
            raise_on_status=False,  # 让我们自己处理状态码
        )

        # 创建会话并配置适配器
        self.session = requests.Session()
        adapter = HTTPAdapter(
            max_retries=retry_strategy, pool_connections=10, pool_maxsize=20
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # 设置默认请求头
        self.default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "RAGFlow-SDK/0.1.0",
        }

        if api_key:
            self.default_headers["Authorization"] = f"Bearer {api_key}"

        if default_headers:
            self.default_headers.update(default_headers)

    def _build_url(self, endpoint: str) -> str:
        """
        构建完整的 URL

        Args:
            endpoint: API 端点路径（例如：/datasets 或 datasets）

        Returns:
            完整的 URL
        """
        return urljoin(self.base_url + "/", endpoint.lstrip("/"))

    def _merge_headers(
        self, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        合并默认请求头和自定义请求头

        Args:
            headers: 自定义请求头

        Returns:
            合并后的请求头
        """
        if headers:
            merged = self.default_headers.copy()
            merged.update(headers)
            return merged
        return self.default_headers

    def _handle_response(self, response: requests.Response) -> requests.Response:
        """
        处理 HTTP 响应，检查错误状态码

        Args:
            response: 响应对象

        Returns:
            响应对象（如果成功）

        Raises:
            HTTPError: HTTP 错误
            TimeoutError: 超时错误
        """
        # 检查是否超时
        if response.status_code == 408:
            raise TimeoutError(
                message="请求超时",
                timeout=self.timeout,
                details={"url": response.url},
            )

        # 检查 HTTP 错误状态码
        if response.status_code >= 400:
            error_message = self._extract_error_message(response)
            raise HTTPError(
                message=error_message,
                status_code=response.status_code,
                response_body=response.text,
                request_url=response.url,
                request_method=(
                    response.request.method
                    if hasattr(response.request, "method")
                    else None
                ),
            )

        return response

    def _extract_error_message(self, response: requests.Response) -> str:
        """
        从响应中提取错误消息

        Args:
            response: HTTP 响应对象

        Returns:
            错误消息字符串
        """
        status_code = response.status_code

        # 尝试解析 JSON 响应
        try:
            data = response.json()
            if isinstance(data, dict):
                # 尝试常见的错误消息字段
                for field in ["message", "error", "detail", "msg"]:
                    if field in data:
                        return str(data[field])
                # 如果没有找到明确的错误消息，返回整个响应
                if "code" in data:
                    return f"API 返回错误码 {data['code']}"
        except (json.JSONDecodeError, ValueError):
            pass

        # 根据 HTTP 状态码返回通用错误消息
        status_messages = {
            400: "请求参数错误",
            401: "未授权，请检查 API Key",
            403: "权限不足",
            404: "资源不存在",
            409: "资源冲突",
            429: "请求过于频繁",
            500: "服务器内部错误",
            502: "网关错误",
            503: "服务不可用",
            504: "网关超时",
        }

        return status_messages.get(status_code, f"HTTP {status_code} 错误")

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> requests.Response:
        """
        发送 HTTP 请求

        Args:
            method: HTTP 方法（GET, POST, PUT, DELETE, PATCH 等）
            endpoint: API 端点
            params: URL 查询参数
            data: 表单数据
            json: JSON 数据
            headers: 额外的请求头
            timeout: 请求超时时间（覆盖默认值）
            **kwargs: 其他 requests 参数

        Returns:
            响应对象

        Raises:
            HTTPError: 请求失败时抛出
            TimeoutError: 请求超时时抛出
        """
        url = self._build_url(endpoint)
        merged_headers = self._merge_headers(headers)
        request_timeout = timeout or self.timeout

        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                params=params,
                data=data,
                json=json,
                headers=merged_headers,
                timeout=request_timeout,
                verify=self.verify_ssl,
                **kwargs,
            )

            # 处理响应并检查错误
            return self._handle_response(response)

        except Timeout:
            # requests.Timeout（底层超时）
            raise TimeoutError(
                message=f"请求超时（{request_timeout}秒）",
                timeout=request_timeout,
                details={"url": url, "method": method},
            )
        except RequestException as e:
            # 其他请求异常
            raise HTTPError(
                message=f"请求失败: {str(e)}",
                details={
                    "url": url,
                    "method": method,
                    "exception_type": type(e).__name__,
                },
                original_error=e,
            )

    def get(
        self,
        endpoint: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> requests.Response:
        """发送 GET 请求"""
        return self.request("GET", endpoint, params=params, headers=headers, **kwargs)

    def post(
        self,
        endpoint: str,
        *,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> requests.Response:
        """发送 POST 请求"""
        return self.request(
            "POST", endpoint, data=data, json=json, headers=headers, **kwargs
        )

    def put(
        self,
        endpoint: str,
        *,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> requests.Response:
        """发送 PUT 请求"""
        return self.request(
            "PUT", endpoint, data=data, json=json, headers=headers, **kwargs
        )

    def patch(
        self,
        endpoint: str,
        *,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> requests.Response:
        """发送 PATCH 请求"""
        return self.request(
            "PATCH", endpoint, data=data, json=json, headers=headers, **kwargs
        )

    def delete(
        self,
        endpoint: str,
        *,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> requests.Response:
        """发送 DELETE 请求"""
        return self.request(
            "DELETE", endpoint, data=data, json=json, headers=headers, **kwargs
        )

    def close(self):
        """关闭会话，释放资源"""
        self.session.close()

    def __enter__(self):
        """支持上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时关闭会话"""
        self.close()

    def __del__(self):
        """析构时关闭会话"""
        self.close()
