"""
测试 source_dispath_srvice 中的 Dify 工厂集成
"""

import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.services.source_dispath_srvice import (
    handle_source_dispatch,
    _get_solid_resource_instruction
)
from src.models.schemas import SourceDispatchRequest
from src.services.log_manager import LogManager


class TestSourceDispatchDifyIntegration:
    """测试资源调度服务中的 Dify 工厂集成"""

    @pytest.fixture
    def mock_env(self):
        """模拟环境变量"""
        env_vars = {
            "DIFY_CHAT_APIKEY_GENRAL_CHAT": "test-key-general",
            "DIFY_CHAT_APIKEY_SOLID_RESOURCE_INSTRUCTION": "test-key-solid",
            "DIFY_BASE_RUL": "http://test.example.com/v1",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            # 重置全局工厂实例
            import src.services.dify_client_factory as factory_module
            factory_module._factory_instance = None
            yield env_vars

    @pytest.fixture
    def log_manager(self):
        """创建日志管理器"""
        from src.config.settings import settings
        return LogManager(settings.logging)

    @pytest.fixture
    def sample_request(self):
        """创建示例请求"""
        return SourceDispatchRequest(
            accidentId="123",
            sourceType="emergencySupplies",
            voiceText="需要应急物资"
        )

    @pytest.mark.asyncio
    async def test_handle_source_dispatch_uses_factory(
        self,
        mock_env,
        log_manager,
        sample_request
    ):
        """测试 handle_source_dispatch 使用工厂获取 client"""
        # Mock DaiShanSQL Server
        with patch('src.services.source_dispath_srvice.Server') as mock_server:
            # Mock 数据库查询结果
            mock_server_instance = MagicMock()
            mock_server.return_value = mock_server_instance
            mock_server_instance.QueryBySQL.return_value = {
                "data": [{
                    "ACCIDENT_NAME": "测试事故",
                    "COORDINATE": "120.0,30.0",
                    "HAZARDOUS_CHEMICALS": "化学品A",
                    "ACCIDENT_OVERVIEW": "事故概述"
                }]
            }

            # Mock DifyClient
            with patch('src.services.dify_client_factory.DifyClient') as mock_dify_client:
                mock_client_instance = MagicMock()
                mock_dify_client.return_value = mock_client_instance

                # Mock Dify 响应
                mock_response = MagicMock()
                mock_response.answer = "answer"
                mock_client_instance.run_chat.return_value = mock_response

                # 调用函数
                result = await handle_source_dispatch(sample_request, log_manager)

                # 验证 DifyClient 被创建（通过工厂）
                assert mock_dify_client.called

    @pytest.mark.asyncio
    async def test_get_solid_resource_instruction_uses_factory(
        self,
        mock_env,
        log_manager,
        sample_request
    ):
        """测试 _get_solid_resource_instruction 使用工厂获取 client"""
        # Mock DifyClient
        with patch('src.services.dify_client_factory.DifyClient') as mock_dify_client:
            mock_client_instance = MagicMock()
            mock_dify_client.return_value = mock_client_instance

            # Mock Dify 响应
            mock_response = MagicMock()
            mock_response.answer = '[{"id":"1"},{"id":"2"}]'
            mock_client_instance.run_chat.return_value = mock_response

            # 调用函数
            result = await _get_solid_resource_instruction(sample_request, log_manager)

            # 验证 DifyClient 被创建（通过工厂）
            assert mock_dify_client.called
            # 验证返回结果
            assert result == '[{"id":"1"},{"id":"2"}]'

    @pytest.mark.asyncio
    async def test_handle_source_dispatch_missing_client(
        self,
        log_manager,
        sample_request
    ):
        """测试缺少 client 配置时的错误处理"""
        # 清空环境变量
        with patch.dict(os.environ, {}, clear=True):
            # 重置全局工厂实例
            import src.services.dify_client_factory as factory_module
            factory_module._factory_instance = None

            # Mock DaiShanSQL Server
            with patch('src.services.source_dispath_srvice.Server') as mock_server:
                mock_server_instance = MagicMock()
                mock_server.return_value = mock_server_instance
                mock_server_instance.QueryBySQL.return_value = {
                    "data": [{
                        "ACCIDENT_NAME": "测试事故",
                        "COORDINATE": "120.0,30.0",
                        "HAZARDOUS_CHEMICALS": "化学品A",
                        "ACCIDENT_OVERVIEW": "事故概述"
                    }]
                }

                # 调用函数
                result = await handle_source_dispatch(sample_request, log_manager)

                # 验证返回错误
                assert result["code"] == 1
                assert "未配置" in result["message"]
