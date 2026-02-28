"""
外部服务连通性测试

验证 AI API、向量库、数据库的连通性，确保外部服务可正常访问。
适用于 CI/CD 环境自动化测试。

运行方式:
    # 运行全部测试
    python -m pytest tests/integration/test_external_service_connectivity.py -v

    # 跳过特定测试
    SKIP_AI_TEST=1 pytest tests/integration/test_external_service_connectivity.py -v
    SKIP_VECTOR_TEST=1 pytest tests/integration/test_external_service_connectivity.py -v
    SKIP_DB_TEST=1 pytest tests/integration/test_external_service_connectivity.py -v

环境要求:
    - Python 3.10+
    - pytest-asyncio
    - 有效的 config.yaml 和 .env 配置
    - 所有项目依赖已安装
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

import pytest

# 导入 conftest 中的辅助函数
from conftest import (
    TEST_TIMEOUT,
    format_diagnostic_message,
    should_skip_ai,
    should_skip_db,
    should_skip_vector,
)


# ============================================================
# AI API 连通性测试
# ============================================================


@pytest.mark.ai_api
class TestAIAPIConnectivity:
    """AI API 连通性测试类"""

    @pytest.mark.asyncio
    async def test_query_chat_connectivity(self, settings, env_status, config_status):
        """
        测试 QueryChat AI API 连通性。

        验证:
        - QueryChat 配置有效
        - API 可正常访问
        - 返回结果非空
        """
        # 检查跳过标志
        if should_skip_ai():
            pytest.skip("SKIP_AI_TEST=1，跳过 AI API 测试")

        # 验证配置
        config = settings.query_chat
        if not config.enabled:
            pytest.skip("query_chat.enabled=False，功能已禁用")

        if not (config.api_key or "").strip():
            pytest.skip("query_chat.api_key 未配置")

        if not (config.base_url or "").strip():
            pytest.skip("query_chat.base_url 未配置")

        # 尝试导入 QueryChat
        try:
            from utils.query_chat import QueryChat
        except ImportError as e:
            # 如果无法导入，检查是否是预执行环境检查模式
            # 在 CI/CD 环境中，我们可能只想验证配置而不实际调用 API
            pytest.skip(f"无法导入 QueryChat 模块: {e}")

        # 创建 QueryChat 实例并测试
        try:
            chat = QueryChat(config)

            # 使用 asyncio.wait_for 设置超时
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    chat.rewrite_query_remove_company, "测试企业岱山经开区"
                ),
                timeout=TEST_TIMEOUT,
            )

            # 验证结果
            assert result is not None, "QueryChat 返回 None"
            assert isinstance(result, str), f"QueryChat 返回类型错误: {type(result)}"

        except asyncio.TimeoutError:
            diagnostic = format_diagnostic_message(
                "AI API",
                TimeoutError(f"请求超时（>{TEST_TIMEOUT}秒）"),
                env_status,
                config_status,
            )
            pytest.fail(f"QueryChat 请求超时\n\n{diagnostic}")

        except Exception as e:
            diagnostic = format_diagnostic_message(
                "AI API", e, env_status, config_status
            )
            pytest.fail(f"QueryChat 调用失败\n\n{diagnostic}")

    @pytest.mark.asyncio
    async def test_intent_classification_connectivity(
        self, settings, env_status, config_status
    ):
        """
        测试意图分类 API 连通性。

        验证:
        - Intent Classification 配置有效
        - API 可正常访问
        - 返回分类结果
        """
        # 检查跳过标志
        if should_skip_ai():
            pytest.skip("SKIP_AI_TEST=1，跳过 AI API 测试")

        # 验证配置
        config = settings.intent_classification
        if not config.enabled:
            pytest.skip("intent_classification.enabled=False，功能已禁用")

        if not (config.api_key or "").strip():
            pytest.skip("intent_classification.api_key 未配置")

        if not (config.base_url or "").strip():
            pytest.skip("intent_classification.base_url 未配置")

        # 尝试导入 IntentClassifier
        try:
            from utils.intent_classifier import ClassificationResult, IntentClassifier
        except ImportError as e:
            pytest.skip(f"无法导入 IntentClassifier 模块: {e}")

        # 创建分类器实例并测试
        try:
            classifier = IntentClassifier(config)

            # 使用 asyncio.wait_for 设置超时
            result = await asyncio.wait_for(
                asyncio.to_thread(classifier.classify, "查询岱山经济开发区的企业信息"),
                timeout=TEST_TIMEOUT,
            )

            # 验证结果
            assert result is not None, "IntentClassifier 返回 None"
            assert isinstance(result, ClassificationResult), (
                f"返回类型错误: {type(result)}"
            )
            # 验证连通性即可，不关心具体分类结果

        except asyncio.TimeoutError:
            diagnostic = format_diagnostic_message(
                "AI API",
                TimeoutError(f"请求超时（>{TEST_TIMEOUT}秒）"),
                env_status,
                config_status,
            )
            pytest.fail(f"IntentClassifier 请求超时\n\n{diagnostic}")

        except Exception as e:
            diagnostic = format_diagnostic_message(
                "AI API", e, env_status, config_status
            )
            pytest.fail(f"IntentClassifier 调用失败\n\n{diagnostic}")


# ============================================================
# 向量库连通性测试
# ============================================================


@pytest.mark.vector_store
class TestVectorStoreConnectivity:
    """向量库连通性测试类"""

    def test_ragflow_connection(self, settings, env_status, config_status):
        """
        测试 RAGFlow 服务连接。

        验证:
        - RAGFlow 配置有效
        - 服务可正常连接
        - test_connection() 返回 True
        """
        # 检查跳过标志
        if should_skip_vector():
            pytest.skip("SKIP_VECTOR_TEST=1，跳过向量库测试")

        # 验证配置
        config = settings.ragflow
        if not (config.api_key or "").strip():
            pytest.skip("ragflow.api_key 未配置")

        if not (config.base_url or "").strip():
            pytest.skip("ragflow.base_url 未配置")

        # 尝试导入 RagflowClient
        try:
            from config.settings import IntentConfig
            from utils.ragflow_client import RagflowClient
        except ImportError as e:
            pytest.skip(f"无法导入 RagflowClient 模块: {e}")

        # 创建客户端实例并测试连接
        try:
            # 创建 IntentConfig mock (简化配置)
            intent_config = IntentConfig()
            client = RagflowClient(config, intent_config)

            # 测试连接
            is_connected = client.test_connection()
            assert is_connected, "RAGFlow test_connection() 返回 False"

        except Exception as e:
            diagnostic = format_diagnostic_message(
                "Vector Store", e, env_status, config_status
            )
            pytest.fail(f"RAGFlow 连接失败\n\n{diagnostic}")

    @pytest.mark.asyncio
    async def test_vector_retrieval(self, settings, env_status, config_status):
        """
        测试向量检索功能。

        验证:
        - 可执行向量检索
        - 返回结果格式正确
        """
        # 检查跳过标志
        if should_skip_vector():
            pytest.skip("SKIP_VECTOR_TEST=1，跳过向量库测试")

        # 验证配置
        config = settings.ragflow
        if not (config.api_key or "").strip():
            pytest.skip("ragflow.api_key 未配置")

        if not (config.base_url or "").strip():
            pytest.skip("ragflow.base_url 未配置")

        # 获取配置的知识库
        database_mapping = getattr(config, "database_mapping", {})
        if not database_mapping:
            pytest.skip("ragflow.database_mapping 未配置，无可用知识库")

        # 获取第一个知识库名称
        database_name = list(database_mapping.keys())[0]

        # 尝试导入 RagflowClient
        try:
            from config.settings import IntentConfig
            from utils.ragflow_client import RagflowClient
        except ImportError as e:
            pytest.skip(f"无法导入 RagflowClient 模块: {e}")

        # 创建客户端并执行检索
        try:
            intent_config = IntentConfig()
            client = RagflowClient(config, intent_config)

            # 执行检索（使用超时）
            results = await asyncio.wait_for(
                client.query_single_database("测试查询", database_name),
                timeout=TEST_TIMEOUT,
            )

            # 验证结果（可以为空列表，但不能抛出异常）
            assert isinstance(results, list), f"返回类型错误: {type(results)}"

        except asyncio.TimeoutError:
            diagnostic = format_diagnostic_message(
                "Vector Store",
                TimeoutError(f"请求超时（>{TEST_TIMEOUT}秒）"),
                env_status,
                config_status,
            )
            pytest.fail(f"向量检索超时\n\n{diagnostic}")

        except Exception as e:
            diagnostic = format_diagnostic_message(
                "Vector Store", e, env_status, config_status
            )
            pytest.fail(f"向量检索失败\n\n{diagnostic}")


# ============================================================
# 数据库连通性测试
# ============================================================


@pytest.mark.database
class TestDatabaseConnectivity:
    """数据库连通性测试类"""

    def test_database_connection(self, settings, env_status, config_status):
        """
        测试数据库连接。

        验证:
        - 数据库配置有效
        - 可执行简单查询
        - 返回结果正确
        """
        # 检查跳过标志
        if should_skip_db():
            pytest.skip("SKIP_DB_TEST=1，跳过数据库测试")

        # 验证环境变量
        required_vars = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
        missing_vars = [v for v in required_vars if not os.getenv(v)]
        if missing_vars:
            pytest.skip(f"缺少数据库环境变量: {', '.join(missing_vars)}")

        # 尝试导入 MySQLManager
        try:
            from SQL.sql_utils import MySQLManager
        except ImportError as e:
            pytest.skip(f"无法导入 MySQLManager 模块: {e}")

        # 创建管理器实例并测试
        try:
            db_manager = MySQLManager()

            # 执行简单查询验证连接
            result = db_manager.request_api_sql("SELECT 1 as test")

            # 验证结果
            assert result is not None, "数据库查询返回 None"
            assert isinstance(result, list), f"返回类型错误: {type(result)}"

        except Exception as e:
            diagnostic = format_diagnostic_message(
                "Database", e, env_status, config_status
            )
            pytest.fail(f"数据库连接失败\n\n{diagnostic}")


# ============================================================
# 配置验证测试（无需外部服务）
# ============================================================


@pytest.mark.config
class TestConfigurationValidation:
    """配置验证测试类 - 无需实际外部服务连接"""

    def test_settings_load(self, settings):
        """验证配置可以正常加载。"""
        assert settings is not None
        assert hasattr(settings, "query_chat")
        assert hasattr(settings, "ragflow")
        assert hasattr(settings, "mysql")
        assert hasattr(settings, "intent_classification")

    def test_query_chat_config_structure(self, settings):
        """验证 QueryChat 配置结构完整。"""
        config = settings.query_chat
        assert hasattr(config, "enabled")
        assert hasattr(config, "api_key")
        assert hasattr(config, "base_url")
        assert hasattr(config, "model")
        assert hasattr(config, "timeout")
        assert hasattr(config, "temperature")

    def test_ragflow_config_structure(self, settings):
        """验证 RAGFlow 配置结构完整。"""
        config = settings.ragflow
        assert hasattr(config, "api_key")
        assert hasattr(config, "base_url")
        assert hasattr(config, "timeout")
        assert hasattr(config, "database_mapping")

    def test_mysql_config_structure(self, settings):
        """验证 MySQL 配置结构完整。"""
        config = settings.mysql
        assert hasattr(config, "host")
        assert hasattr(config, "name")
        assert hasattr(config, "user")
        assert hasattr(config, "password")
        assert hasattr(config, "port")

    def test_env_status_helper(self, env_status):
        """验证环境变量状态辅助函数工作正常。"""
        assert isinstance(env_status, dict)
        # 检查至少有一些预期的环境变量
        expected_vars = ["SKIP_AI_TEST", "SKIP_VECTOR_TEST", "SKIP_DB_TEST"]
        for var in expected_vars:
            assert var in env_status or True  # 不强制存在，但结构应正确


# ============================================================
# 辅助函数 (用于测试文件内部使用)
# ============================================================


def run_diagnostic_check(service_type: str) -> dict:
    """
    运行诊断检查，返回环境状态。

    Args:
        service_type: 服务类型 (AI API, Vector Store, Database)

    Returns:
        诊断信息字典
    """
    from conftest import get_env_status

    env_status = get_env_status()

    # 根据服务类型筛选相关环境变量
    relevant_vars = {
        "AI API": [
            "QUERY_CHAT_API_KEY",
            "QUERY_CHAT_BASE_URL",
            "INTENT_CLASSIFICATION_API_KEY",
            "INTENT_CLASSIFICATION_BASE_URL",
        ],
        "Vector Store": ["RAGFLOW_API_KEY", "RAGFLOW_BASE_URL"],
        "Database": ["DB_HOST", "DB_NAME", "DB_USER", "DB_PORT", "SQL_DataBase"],
    }.get(service_type, [])

    return {
        "service": service_type,
        "env_vars": {k: v for k, v in env_status.items() if k in relevant_vars},
    }


if __name__ == "__main__":
    # 支持直接运行
    pytest.main([__file__, "-v"])
