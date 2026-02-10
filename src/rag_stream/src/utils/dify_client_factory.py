"""
Dify Client 工厂类

自动从环境变量加载所有 DIFY_CHAT_APIKEY_ 前缀的配置，
并提供统一的 client 访问接口。
"""

import os
from typing import Dict, Optional

from dify_sdk import DifyClient


class DifyClientFactory:
    """
    Dify Client 工厂类

    自动读取环境变量中所有 DIFY_CHAT_APIKEY_ 前缀的配置，
    使用后缀作为 client 名称，提供统一的 client 访问接口。

    示例:
        环境变量: DIFY_CHAT_APIKEY_PERSONNEL_DISPATCHING=xxx
        client 名称: PERSONNEL_DISPATCHING

        factory = DifyClientFactory()
        client = factory.get_client("PERSONNEL_DISPATCHING")
    """

    _ENV_PREFIX = "DIFY_CHAT_APIKEY_"
    _BASE_URL_ENV = "DIFY_BASE_RUL"
    _DEFAULT_BASE_URL = "http://172.16.11.60/v1"

    def __init__(self, base_url: Optional[str] = None):
        """
        初始化工厂

        Args:
            base_url: Dify API Base URL，如果不提供则从环境变量读取
        """
        self._base_url = base_url or os.getenv(
            self._BASE_URL_ENV,
            self._DEFAULT_BASE_URL
        )
        self._clients: Dict[str, DifyClient] = {}
        self._api_keys: Dict[str, str] = {}
        self._load_api_keys_from_env()

    def _load_api_keys_from_env(self) -> None:
        """从环境变量加载所有 DIFY_CHAT_APIKEY_ 前缀的配置"""
        for key, value in os.environ.items():
            if key.startswith(self._ENV_PREFIX) and value:
                # 提取后缀作为 client 名称
                client_name = key[len(self._ENV_PREFIX):]
                self._api_keys[client_name] = value

    def _create_client(self, api_key: str) -> DifyClient:
        """
        创建 DifyClient 实例

        Args:
            api_key: API Key

        Returns:
            DifyClient 实例
        """
        return DifyClient(api_key=api_key, base_url=self._base_url)

    def get_client(self, name: str) -> DifyClient:
        """
        获取指定名称的 client

        Args:
            name: client 名称（环境变量后缀）

        Returns:
            DifyClient 实例

        Raises:
            ValueError: 如果指定名称的 client 不存在
        """
        if name not in self._api_keys:
            raise ValueError(
                f"Client '{name}' 不存在。"
                f"可用的 client: {', '.join(self.list_clients())}"
            )

        # 懒加载：只在第一次访问时创建 client
        if name not in self._clients:
            self._clients[name] = self._create_client(self._api_keys[name])

        return self._clients[name]

    def list_clients(self) -> list[str]:
        """
        列出所有可用的 client 名称

        Returns:
            client 名称列表
        """
        return list(self._api_keys.keys())

    def has_client(self, name: str) -> bool:
        """
        检查是否存在指定名称的 client

        Args:
            name: client 名称

        Returns:
            如果存在返回 True，否则返回 False
        """
        return name in self._api_keys


# ============================================================
# 全局工厂实例
# ============================================================

# 全局 DifyClientFactory 实例，在模块加载时自动初始化
_factory_instance: Optional[DifyClientFactory] = None


def get_factory() -> DifyClientFactory:
    """
    获取全局 DifyClientFactory 实例

    Returns:
        DifyClientFactory 实例
    """
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = DifyClientFactory()
    return _factory_instance


def get_client(name: str) -> DifyClient:
    """
    获取指定名称的 Dify client（便捷方法）

    Args:
        name: client 名称

    Returns:
        DifyClient 实例

    Raises:
        ValueError: 如果指定名称的 client 不存在
    """
    return get_factory().get_client(name)


def list_clients() -> list[str]:
    """
    列出所有可用的 client 名称（便捷方法）

    Returns:
        client 名称列表
    """
    return get_factory().list_clients()
