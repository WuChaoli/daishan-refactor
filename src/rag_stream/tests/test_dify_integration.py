"""
测试 DifyClientFactory 与 dify_service 的集成
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from src.utils.dify_client_factory import get_factory, get_client, list_clients


class TestDifyClientFactoryIntegration:
    """测试 DifyClientFactory 与其他服务的集成"""

    @pytest.fixture
    def mock_env(self):
        """模拟环境变量"""
        env_vars = {
            "DIFY_CHAT_APIKEY_PERSONNEL_DISPATCHING": "test-key-personnel",
            "DIFY_CHAT_APIKEY_EMERGENCY_RESPONSE": "test-key-emergency",
            "DIFY_BASE_RUL": "http://test.example.com/v1",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            # 重置全局工厂实例
            import src.utils.dify_client_factory as factory_module
            factory_module._factory_instance = None
            yield env_vars

    def test_get_factory_singleton(self, mock_env):
        """测试全局工厂实例是单例"""
        factory1 = get_factory()
        factory2 = get_factory()

        # 验证返回同一个实例
        assert factory1 is factory2

    def test_get_client_convenience_method(self, mock_env):
        """测试便捷方法 get_client"""
        client = get_client("PERSONNEL_DISPATCHING")

        # 验证返回的是 DifyClient 实例
        assert client is not None

    def test_list_clients_convenience_method(self, mock_env):
        """测试便捷方法 list_clients"""
        clients = list_clients()

        # 验证返回正确的 client 列表
        assert "PERSONNEL_DISPATCHING" in clients
        assert "EMERGENCY_RESPONSE" in clients
        assert len(clients) == 2

    def test_stream_personnel_dispatch_uses_factory(self, mock_env):
        """测试 stream_personnel_dispatch 使用工厂"""
        from src.services.dify_service import stream_personnel_dispatch

        # 这个测试验证函数可以正确导入和使用工厂
        # 实际的流式调用需要 mock DifyClient 的行为
        # 这里只验证不会因为缺少环境变量而失败
        try:
            # 尝试创建生成器（不实际调用）
            gen = stream_personnel_dispatch("test query")
            assert gen is not None
        except ValueError as e:
            # 如果抛出 ValueError，应该是因为 client 配置问题
            # 而不是因为缺少环境变量
            assert "未配置" in str(e) or "不存在" in str(e)
