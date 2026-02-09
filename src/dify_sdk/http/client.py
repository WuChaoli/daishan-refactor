"""
Dify SDK HTTP 客户端

封装 requests.Session,提供统一的 HTTP 请求接口,
支持自动重试、超时处理和错误处理。
"""

import time
from typing import Any, Dict, Optional

import requests

from ..core.exceptions import DifyAPIError, DifyConnectionError


class HTTPClient:
    """
    HTTP 客户端类

    封装 requests.Session,提供统一的 HTTP 请求接口。
    支持自动重试、超时处理和错误处理。

    Attributes:
        config: 配置对象
        session: requests.Session 对象
    """

    def __init__(
        self, base_url: str, api_key: str, timeout: int = 30, max_retries: int = 3
    ):
        """
        初始化 HTTP 客户端

        Args:
            base_url: API Base URL
            api_key: Dify API Key
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

        # 创建 Session
        self.session = requests.Session()

        # 设置默认请求头
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "DifyPythonSDK/1.0.0",
            }
        )

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """
        发送 GET 请求

        Args:
            endpoint: API 端点 (如 /v1/workflows/tasks/{id})
            params: 查询参数

        Returns:
            requests.Response: 响应对象

        Raises:
            DifyConnectionError: 网络连接错误 (重试后仍失败)
            DifyAPIError: API 返回错误状态码
        """
        url = f"{self.base_url}{endpoint}"
        return self._request_with_retry("GET", url, params=params)

    def post(
        self, endpoint: str, json: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """
        发送 POST 请求

        Args:
            endpoint: API 端点
            json: 请求体 (JSON 格式)

        Returns:
            requests.Response: 响应对象

        Raises:
            DifyConnectionError: 网络连接错误 (重试后仍失败)
            DifyAPIError: API 返回错误状态码
        """
        url = f"{self.base_url}{endpoint}"
        return self._request_with_retry("POST", url, json=json)

    def post_stream(
        self, endpoint: str, json: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """
        发送 POST 请求 (流式响应)

        用于 SSE (Server-Sent Events) 等流式响应场景。

        Args:
            endpoint: API 端点
            json: 请求体 (JSON 格式)

        Returns:
            requests.Response: 响应对象 (可迭代读取行)

        Raises:
            DifyConnectionError: 网络连接错误
            DifyAPIError: API 返回错误状态码
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.post(
                url, json=json, timeout=self.timeout, stream=True  # 启用流式响应
            )

            # 检查状态码
            if response.status_code >= 400:
                error_msg = f"API 错误: {response.text}"
                try:
                    error_data = response.json()
                except:
                    error_data = None

                raise DifyAPIError(
                    message=error_msg,
                    status_code=response.status_code,
                    response=error_data,
                )

            return response

        except requests.exceptions.RequestException as e:
            raise DifyConnectionError(
                message=f"HTTP POST 请求失败: {str(e)}", original_error=e
            )

    def get_stream(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """
        发送 GET 请求 (流式响应)

        用于 SSE (Server-Sent Events) 等流式响应场景。

        Args:
            endpoint: API 端点 (如 /v1/workflows/logs)
            params: 查询参数

        Returns:
            requests.Response: 响应对象 (可迭代读取行)

        Raises:
            DifyConnectionError: 网络连接错误
            DifyAPIError: API 返回错误状态码
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.get(
                url, params=params, timeout=self.timeout, stream=True  # 启用流式响应
            )

            # 检查状态码
            if response.status_code >= 400:
                error_msg = f"API 错误: {response.text}"
                try:
                    error_data = response.json()
                except:
                    error_data = None

                raise DifyAPIError(
                    message=error_msg,
                    status_code=response.status_code,
                    response=error_data,
                )

            return response

        except requests.exceptions.RequestException as e:
            raise DifyConnectionError(
                message=f"HTTP GET 请求失败: {str(e)}", original_error=e
            )

    def post_multipart(self, endpoint: str, files: Dict[str, Any]) -> requests.Response:
        """
        发送 POST 请求 (multipart/form-data)

        用于文件上传等场景。

        Args:
            endpoint: API 端点
            files: 文件字典 (requests 格式)

        Returns:
            requests.Response: 响应对象

        Raises:
            DifyConnectionError: 网络连接错误
            DifyAPIError: API 返回错误状态码
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.post(url, files=files, timeout=self.timeout)

            # 检查状态码
            if response.status_code >= 400:
                error_msg = f"API 错误: {response.text}"
                try:
                    error_data = response.json()
                except:
                    error_data = None

                raise DifyAPIError(
                    message=error_msg,
                    status_code=response.status_code,
                    response=error_data,
                )

            return response

        except requests.exceptions.RequestException as e:
            raise DifyConnectionError(
                message=f"HTTP POST (multipart) 请求失败: {str(e)}", original_error=e
            )

    def close(self):
        """
        关闭 Session

        释放网络连接资源。
        """
        self.session.close()

    def _request_with_retry(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """
        发送 HTTP 请求 (带重试机制)

        仅对网络错误进行重试,API 错误 (4xx, 5xx) 不重试。
        使用指数退避策略: 1s, 2s, 4s...

        Args:
            method: HTTP 方法 (GET/POST)
            url: 完整 URL
            params: 查询参数
            json: 请求体

        Returns:
            requests.Response: 响应对象

        Raises:
            DifyConnectionError: 网络错误 (重试后仍失败)
            DifyAPIError: API 错误
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                # 发送请求
                if method == "GET":
                    response = self.session.get(
                        url, params=params, timeout=self.timeout
                    )
                elif method == "POST":
                    response = self.session.post(
                        url, params=params, json=json, timeout=self.timeout
                    )
                else:
                    raise ValueError(f"不支持的 HTTP 方法: {method}")

                # 检查状态码
                if response.status_code >= 400:
                    error_msg = f"API 错误: {response.text}"
                    try:
                        error_data = response.json()
                    except:
                        error_data = None

                    raise DifyAPIError(
                        message=error_msg,
                        status_code=response.status_code,
                        response=error_data,
                    )

                # 成功: 返回响应
                return response

            except DifyAPIError:
                # API 错误不重试,直接抛出
                raise

            except requests.exceptions.RequestException as e:
                # 网络错误: 记录并可能重试
                last_exception = e

                if attempt < self.max_retries:
                    # 计算退避时间: 1s, 2s, 4s...
                    backoff_time = 2**attempt
                    time.sleep(backoff_time)
                else:
                    # 重试次数耗尽
                    raise DifyConnectionError(
                        message=f"HTTP {method} 请求失败 (已重试 {self.max_retries} 次): {str(e)}",
                        original_error=e,
                    )

        # 理论上不会执行到这里
        if last_exception:
            raise DifyConnectionError(
                message=f"HTTP {method} 请求失败: {str(last_exception)}",
                original_error=last_exception,
            )

        # 满足类型检查器
        raise DifyConnectionError(
            message=f"HTTP {method} 请求失败: Unknown error",
            original_error=None,
        )

    def __enter__(self):
        """支持上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时关闭连接"""
        self.close()
