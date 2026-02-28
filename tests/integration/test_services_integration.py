"""
集成测试：验证 rag_stream 和 Digital_human_command_interface 服务启动和API调用

测试范围：
1. rag_stream 服务健康检查和主要API端点
2. Digital_human_command_interface 服务健康检查和主要API端点
3. 服务间依赖检查

使用 FastAPI TestClient 进行测试，无需启动真实服务。
此测试设计为在提交前运行，不依赖外部服务（RAGFlow、Dify等）。

运行方式:
    cd /home/wuchaoli/codespace/daishan-refactor
    python -m pytest tests/integration/test_services_integration.py -v

环境要求:
    - Python 3.10+
    - FastAPI
    - pytest
    - httpx
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient


def setup_test_environment():
    """设置测试环境，确保路径和mock配置正确。"""
    project_root = Path(__file__).parent.parent.parent

    src_paths = [
        project_root / "src",
        project_root / "src" / "rag_stream" / "src",
        project_root / "src" / "DaiShanSQL" / "DaiShanSQL",
    ]

    for path in src_paths:
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))

    os.environ.setdefault("RAGFLOW_API_KEY", "test-key")
    os.environ.setdefault("DIFY_API_KEY", "test-key")


setup_test_environment()


class TestRagStreamService:
    """rag_stream 服务集成测试"""

    @pytest.fixture
    def rag_stream_app(self):
        """创建 rag_stream FastAPI 应用实例，mock外部依赖。"""
        from rag_stream.src.main import app

        with patch("rag_stream.src.main.RagflowClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.test_connection.return_value = True
            mock_client.return_value = mock_instance

            with patch("rag_stream.src.main.IntentService") as mock_intent:
                mock_intent_instance = MagicMock()
                mock_intent.return_value = mock_intent_instance

                yield app

    @pytest.fixture
    def rag_stream_client(self, rag_stream_app) -> TestClient:
        """创建 rag_stream TestClient。"""
        return TestClient(rag_stream_app)

    def test_health_endpoint(self, rag_stream_client):
        """测试健康检查端点是否正常响应。"""
        response = rag_stream_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"

    def test_categories_endpoint(self, rag_stream_client):
        """测试获取分类列表端点。"""
        response = rag_stream_client.get("/api/categories")

        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)

    def test_chat_request_validation(self, rag_stream_client):
        """测试聊天请求参数验证。"""
        invalid_payload = {
            "question": "",
            "user_id": "test_user",
        }

        response = rag_stream_client.post(
            "/api/general",
            json=invalid_payload
        )

        assert response.status_code in [400, 422]

    def test_sessions_endpoints(self, rag_stream_client):
        """测试会话管理端点。"""
        response = rag_stream_client.get("/api/sessions")
        assert response.status_code == 200


class TestDigitalHumanService:
    """Digital_human_command_interface 服务集成测试"""

    @pytest.fixture
    def digital_human_app(self):
        """创建 Digital_human_command_interface FastAPI 应用实例，mock外部依赖。"""
        from Digital_human_command_interface.main import app

        mock_config = MagicMock()
        mock_config.server_host = "0.0.0.0"
        mock_config.server_port = 11029
        mock_config.stream_chat_timeout = 30.0

        with patch("Digital_human_command_interface.main.ConfigManager") as mock_config_mgr:
            mock_config_mgr.return_value.get_config.return_value = mock_config

            with patch("Digital_human_command_interface.main.RagflowClient") as mock_client:
                mock_instance = MagicMock()
                mock_instance.test_connection.return_value = True
                mock_client.return_value = mock_instance

                yield app

    @pytest.fixture
    def digital_human_client(self, digital_human_app) -> TestClient:
        """创建 Digital_human_command_interface TestClient。"""
        return TestClient(digital_human_app)

    def test_health_endpoint(self, digital_human_client):
        """测试健康检查端点。"""
        response = digital_human_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_root_endpoint(self, digital_human_client):
        """测试根端点返回服务信息。"""
        response = digital_human_client.get("/")

        assert response.status_code == 200

    def test_intent_endpoint_validation(self, digital_human_client):
        """测试意图识别端点参数验证。"""
        invalid_payload = {
            "text": "",
        }

        response = digital_human_client.post(
            "/intent",
            json=invalid_payload
        )

        assert response.status_code in [400, 422]

    def test_stream_chat_endpoint_validation(self, digital_human_client):
        """测试流式聊天端点参数验证。"""
        invalid_payload = {
            "message": "",
        }

        response = digital_human_client.post(
            "/api/stream-chat",
            json=invalid_payload
        )

        assert response.status_code in [400, 422]


class TestServiceDependencies:
    """服务间依赖测试"""

    def test_rag_stream_imports(self):
        """测试 rag_stream 模块导入是否正常。"""
        try:
            from rag_stream.src.main import app
            from rag_stream.src.routes.chat_routes import router
            from rag_stream.src.config.settings import settings
            from rag_stream.src.services.intent_service import IntentService
            assert True
        except ImportError as e:
            pytest.fail(f"rag_stream 模块导入失败: {e}")

    def test_digital_human_imports(self):
        """测试 Digital_human_command_interface 模块导入是否正常。"""
        try:
            from Digital_human_command_interface.main import app
            from Digital_human_command_interface.src.api.routes import router
            from Digital_human_command_interface.src.config import ConfigManager
            assert True
        except ImportError as e:
            pytest.fail(f"Digital_human_command_interface 模块导入失败: {e}")

    def test_service_ports_configured(self):
        """测试服务端口配置是否正确。"""
        from rag_stream.src.config.settings import settings

        assert settings.server.port == 11028
        assert settings.server.host == "0.0.0.0"


class TestServiceStartupSimulation:
    """服务启动模拟测试 - 验证服务启动流程"""

    @pytest.mark.asyncio
    async def test_rag_stream_lifespan(self):
        """测试 rag_stream 应用生命周期。"""
        from contextlib import asynccontextmanager

        from rag_stream.src.main import lifespan

        mock_app = MagicMock()

        with patch("rag_stream.src.main.RagflowClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.test_connection.return_value = True
            mock_client.return_value = mock_instance

            with patch("rag_stream.src.main.IntentService"):
                async with lifespan(mock_app):
                    pass

    @pytest.mark.asyncio
    async def test_digital_human_lifespan(self):
        """测试 Digital_human_command_interface 应用生命周期。"""
        from Digital_human_command_interface.main import lifespan

        mock_app = MagicMock()
        mock_app.state = MagicMock()

        mock_config = MagicMock()
        mock_config.server_host = "0.0.0.0"
        mock_config.server_port = 11029
        mock_config.stream_chat_timeout = 30.0

        with patch("Digital_human_command_interface.main.ConfigManager") as mock_config_mgr:
            mock_config_mgr.return_value.get_config.return_value = mock_config

            with patch("Digital_human_command_interface.main.RagflowClient") as mock_client:
                mock_instance = MagicMock()
                mock_instance.test_connection.return_value = True
                mock_client.return_value = mock_instance

                async with lifespan(mock_app):
                    pass


class TestAPICompatibility:
    """API兼容性测试"""

    def test_rag_stream_api_structure(self):
        """测试 rag_stream API 结构完整性。"""
        from rag_stream.src.main import app

        routes = [route.path for route in app.routes]

        expected_routes = [
            "/health",
            "/api/general",
            "/api/categories",
            "/api/sessions",
        ]

        for route in expected_routes:
            assert any(route in r for r in routes), f"缺少路由: {route}"

    def test_digital_human_api_structure(self):
        """测试 Digital_human_command_interface API 结构完整性。"""
        from Digital_human_command_interface.main import app

        routes = [route.path for route in app.routes]

        expected_routes = [
            "/health",
            "/intent",
            "/api/stream-chat",
        ]

        for route in expected_routes:
            assert any(route in r for r in routes), f"缺少路由: {route}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
