"""
外部服务连通性测试 - 共享 Fixtures 和配置

提供:
- 共享 pytest fixtures (settings, event_loop)
- 诊断信息收集函数
- 环境变量跳过控制
- 路径自动配置

Usage:
    pytest tests/integration/test_external_service_connectivity.py -v

Environment Variables:
    SKIP_AI_TEST=1 - 跳过 AI API 测试
    SKIP_VECTOR_TEST=1 - 跳过向量库测试
    SKIP_DB_TEST=1 - 跳过数据库测试
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Dict

import pytest


# ============================================================
# 路径配置 (必须在导入项目模块前设置)
# ============================================================


def _setup_project_paths() -> None:
    """设置项目路径，确保可以导入项目模块。"""
    # 当前文件: tests/integration/conftest.py
    # 项目根目录: tests/integration/ -> tests/ -> project_root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent

    paths_to_add = [
        project_root / "src" / "rag_stream" / "src",
        project_root / "src" / "DaiShanSQL" / "DaiShanSQL",
        project_root / "src",
    ]

    for path in paths_to_add:
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


# 立即执行路径配置
_setup_project_paths()


# ============================================================
# 诊断信息辅助函数
# ============================================================


def get_env_status() -> Dict[str, Any]:
    """
    获取环境变量状态（只显示是否设置，不暴露实际值）。

    Returns:
        环境变量状态字典
    """
    env_vars = {
        # AI API 相关
        "QUERY_CHAT_API_KEY": "AI API",
        "QUERY_CHAT_BASE_URL": "AI API",
        "INTENT_CLASSIFICATION_API_KEY": "AI API",
        "INTENT_CLASSIFICATION_BASE_URL": "AI API",
        # 向量库相关
        "RAGFLOW_API_KEY": "Vector Store",
        "RAGFLOW_BASE_URL": "Vector Store",
        # 数据库相关
        "DB_HOST": "Database",
        "DB_NAME": "Database",
        "DB_USER": "Database",
        "DB_PORT": "Database",
        # 跳过控制
        "SKIP_AI_TEST": "Control",
        "SKIP_VECTOR_TEST": "Control",
        "SKIP_DB_TEST": "Control",
    }

    status = {}
    for var, category in env_vars.items():
        value = os.getenv(var)
        status[var] = {
            "category": category,
            "set": value is not None and value.strip() != "",
        }

    return status


def get_config_status(settings) -> Dict[str, Any]:
    """
    获取配置状态（安全地显示配置信息，不暴露敏感数据）。

    Args:
        settings: 加载后的 Settings 实例

    Returns:
        配置状态字典
    """
    return {
        "query_chat": {
            "enabled": getattr(settings.query_chat, "enabled", False),
            "base_url_set": bool(getattr(settings.query_chat, "base_url", "")),
            "model_set": bool(getattr(settings.query_chat, "model", "")),
            "api_key_set": bool(getattr(settings.query_chat, "api_key", "")),
        },
        "intent_classification": {
            "enabled": getattr(settings.intent_classification, "enabled", False),
            "base_url_set": bool(
                getattr(settings.intent_classification, "base_url", "")
            ),
            "model_set": bool(getattr(settings.intent_classification, "model", "")),
            "api_key_set": bool(getattr(settings.intent_classification, "api_key", "")),
        },
        "ragflow": {
            "base_url_set": bool(getattr(settings.ragflow, "base_url", "")),
            "api_key_set": bool(getattr(settings.ragflow, "api_key", "")),
            "database_count": len(getattr(settings.ragflow, "database_mapping", {})),
            "database_names": list(
                getattr(settings.ragflow, "database_mapping", {}).keys()
            ),
        },
        "mysql": {
            "host_set": bool(getattr(settings.mysql, "host", "")),
            "name_set": bool(getattr(settings.mysql, "name", "")),
            "user_set": bool(getattr(settings.mysql, "user", "")),
            "port": getattr(settings.mysql, "port", 3306),
        },
    }


def format_diagnostic_message(
    service: str,
    error: Exception,
    env_status: Dict[str, Any],
    config_status: Dict[str, Any],
) -> str:
    """
    格式化诊断信息消息。

    Args:
        service: 服务名称 (AI API, Vector Store, Database)
        error: 异常对象
        env_status: 环境变量状态
        config_status: 配置状态

    Returns:
        格式化的诊断信息字符串
    """
    lines = [
        f"{service} 连通性测试失败",
        "=" * 50,
        f"错误: {type(error).__name__}: {error}",
        "",
    ]

    # 环境变量检查
    lines.append("环境变量检查:")
    category_map = {
        "AI API": [
            "QUERY_CHAT_API_KEY",
            "QUERY_CHAT_BASE_URL",
            "INTENT_CLASSIFICATION_API_KEY",
            "INTENT_CLASSIFICATION_BASE_URL",
        ],
        "Vector Store": ["RAGFLOW_API_KEY", "RAGFLOW_BASE_URL"],
        "Database": ["DB_HOST", "DB_NAME", "DB_USER", "DB_PORT"],
    }

    relevant_vars = category_map.get(service, [])
    for var in relevant_vars:
        if var in env_status:
            status = "已设置" if env_status[var]["set"] else "未设置"
            lines.append(f"  - {var}: {status}")

    lines.append("")

    # 配置检查
    lines.append("配置检查:")
    if service == "AI API":
        qc = config_status.get("query_chat", {})
        lines.extend(
            [
                f"  query_chat.enabled: {qc.get('enabled', 'N/A')}",
                f"  query_chat.base_url: {'已设置' if qc.get('base_url_set') else '未设置'}",
                f"  query_chat.model: {'已设置' if qc.get('model_set') else '未设置'}",
                f"  query_chat.api_key: {'已设置' if qc.get('api_key_set') else '未设置'}",
            ]
        )
        ic = config_status.get("intent_classification", {})
        lines.extend(
            [
                f"  intent_classification.enabled: {ic.get('enabled', 'N/A')}",
                f"  intent_classification.base_url: {'已设置' if ic.get('base_url_set') else '未设置'}",
            ]
        )
    elif service == "Vector Store":
        rf = config_status.get("ragflow", {})
        lines.extend(
            [
                f"  ragflow.base_url: {'已设置' if rf.get('base_url_set') else '未设置'}",
                f"  ragflow.api_key: {'已设置' if rf.get('api_key_set') else '未设置'}",
                f"  配置的知识库数量: {rf.get('database_count', 0)}",
            ]
        )
        if rf.get("database_names"):
            lines.append(f"  知识库列表: {', '.join(rf['database_names'])}")
    elif service == "Database":
        mysql = config_status.get("mysql", {})
        lines.extend(
            [
                f"  mysql.host: {'已设置' if mysql.get('host_set') else '未设置'}",
                f"  mysql.name: {'已设置' if mysql.get('name_set') else '未设置'}",
                f"  mysql.user: {'已设置' if mysql.get('user_set') else '未设置'}",
                f"  mysql.port: {mysql.get('port', 'N/A')}",
            ]
        )

    lines.append("")
    lines.append("建议:")

    if service == "AI API":
        lines.extend(
            [
                "  - 检查 API 密钥是否有效",
                "  - 检查网络连通性: ping API 服务器地址",
                "  - 确认 config.yaml 中的 query_chat 配置正确",
            ]
        )
    elif service == "Vector Store":
        base_url = ""
        if config_status.get("ragflow", {}).get("base_url_set"):
            # 尝试获取 base_url 主机名
            try:
                from urllib.parse import urlparse

                full_url = os.getenv("RAGFLOW_BASE_URL", "")
                if full_url:
                    parsed = urlparse(full_url)
                    base_url = parsed.hostname or ""
            except Exception:
                pass

        lines.extend(
            [
                "  - 检查 RAGFlow API 密钥是否有效",
                f"  - 检查网络连通性" + (f": ping {base_url}" if base_url else ""),
                "  - 确认 config.yaml 中的 ragflow.database_mapping 配置正确",
            ]
        )
    elif service == "Database":
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "3306")
        lines.extend(
            [
                "  - 检查数据库连接字符串是否正确",
                f"  - 检查网络连通性: telnet {host} {port}",
                "  - 确认数据库用户有权限访问",
                "  - 检查 .env 文件中的数据库配置",
            ]
        )

    return "\n".join(lines)


# ============================================================
# 跳过控制函数
# ============================================================


def should_skip_ai() -> bool:
    """检查是否应该跳过 AI API 测试。"""
    return os.getenv("SKIP_AI_TEST") == "1"


def should_skip_vector() -> bool:
    """检查是否应该跳过向量库测试。"""
    return os.getenv("SKIP_VECTOR_TEST") == "1"


def should_skip_db() -> bool:
    """检查是否应该跳过数据库测试。"""
    return os.getenv("SKIP_DB_TEST") == "1"


# ============================================================
# Pytest Fixtures
# ============================================================


@pytest.fixture(scope="session")
def event_loop():
    """提供会话级别的事件循环。"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def settings():
    """
    提供加载后的 Settings 实例。

    Returns:
        Settings 实例
    """
    try:
        from config.settings import load_settings

        return load_settings()
    except Exception as e:
        pytest.fail(f"加载配置失败: {e}")


@pytest.fixture(scope="session")
def env_status():
    """
    提供环境变量状态。

    Returns:
        环境变量状态字典
    """
    return get_env_status()


@pytest.fixture(scope="session")
def config_status(settings):
    """
    提供配置状态。

    Args:
        settings: settings fixture

    Returns:
        配置状态字典
    """
    return get_config_status(settings)


# ============================================================
# 超时配置
# ============================================================

TEST_TIMEOUT = 10  # 秒


def pytest_configure(config):
    """配置 pytest。"""
    # 添加自定义标记
    config.addinivalue_line("markers", "ai_api: AI API 连通性测试")
    config.addinivalue_line("markers", "vector_store: 向量库连通性测试")
    config.addinivalue_line("markers", "database: 数据库连通性测试")
    config.addinivalue_line("markers", "slow: 慢速测试")
