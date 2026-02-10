"""
测试 DifyClientFactory
"""

import os
import pytest
from unittest.mock import patch

from src.utils.dify_client_factory import DifyClientFactory


class TestDifyClientFactory:
    """测试 DifyClientFactory 类"""

    @pytest.fixture
    def mock_env(self):
        """模拟环境变量"""
        env_vars = {
            "DIFY_CHAT_APIKEY_PERSONNEL_DISPATCHING": "test-key-1",
            "DIFY_CHAT_APIKEY_EMERGENCY_RESPONSE": "test-key-2",
            "DIFY_CHAT_APIKEY_PARK_INFO": "test-key-3",
            "DIFY_BASE_RUL": "http://test.example.com/v1",
            "OTHER_ENV_VAR": "should-be-ignored",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            yield env_vars

    def test_load_api_keys_from_env(self, mock_env):
        """测试从环境变量加载 API keys"""
        factory = DifyClientFactory()

        # 验证加载了正确数量的 client
        assert len(factory.list_clients()) == 3

        # 验证 client 名称正确
        client_names = factory.list_clients()
        assert "PERSONNEL_DISPATCHING" in client_names
        assert "EMERGENCY_RESPONSE" in client_names
        assert "PARK_INFO" in client_names

    def test_get_client_success(self, mock_env):
        """测试成功获取 client"""
        factory = DifyClientFactory()

        # 获取 client
        client = factory.get_client("PERSONNEL_DISPATCHING")

        # 验证 client 不为空
        assert client is not None

        # 验证多次获取返回同一个实例（懒加载 + 缓存）
        client2 = factory.get_client("PERSONNEL_DISPATCHING")
        assert client is client2

    def test_get_client_not_found(self, mock_env):
        """测试获取不存在的 client"""
        factory = DifyClientFactory()

        # 尝试获取不存在的 client
        with pytest.raises(ValueError) as exc_info:
            factory.get_client("NON_EXISTENT")

        # 验证错误消息
        assert "NON_EXISTENT" in str(exc_info.value)
        assert "不存在" in str(exc_info.value)

    def test_has_client(self, mock_env):
        """测试检查 client 是否存在"""
        factory = DifyClientFactory()

        # 验证存在的 client
        assert factory.has_client("PERSONNEL_DISPATCHING") is True
        assert factory.has_client("EMERGENCY_RESPONSE") is True

        # 验证不存在的 client
        assert factory.has_client("NON_EXISTENT") is False

    def test_custom_base_url(self):
        """测试自定义 base_url"""
        custom_url = "http://custom.example.com/v1"
        factory = DifyClientFactory(base_url=custom_url)

        # 验证使用了自定义 URL
        assert factory._base_url == custom_url

    def test_default_base_url(self, mock_env):
        """测试默认 base_url"""
        factory = DifyClientFactory()

        # 验证使用了环境变量中的 URL
        assert factory._base_url == "http://test.example.com/v1"

    def test_empty_env(self):
        """测试空环境变量"""
        with patch.dict(os.environ, {}, clear=True):
            factory = DifyClientFactory()

            # 验证没有加载任何 client
            assert len(factory.list_clients()) == 0

    def test_ignore_empty_api_key(self):
        """测试忽略空的 API key"""
        env_vars = {
            "DIFY_CHAT_APIKEY_VALID": "test-key",
            "DIFY_CHAT_APIKEY_EMPTY": "",  # 空值应该被忽略
        }
        with patch.dict(os.environ, env_vars, clear=True):
            factory = DifyClientFactory()

            # 验证只加载了有效的 client
            assert len(factory.list_clients()) == 1
            assert "VALID" in factory.list_clients()
            assert "EMPTY" not in factory.list_clients()
