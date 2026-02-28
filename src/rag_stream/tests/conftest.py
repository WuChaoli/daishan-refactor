"""
pytest配置文件
为所有测试设置正确的Python路径
"""
import sys
import os
from pathlib import Path

# 获取项目根目录
# tests/ 位于 src/rag_stream/tests/
# 所以需要向上3级到项目根目录
current_dir = Path(__file__).parent
rag_stream_root = current_dir.parent
project_root = rag_stream_root.parent

# 添加src目录到sys.path
src_root = project_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

# 添加DaiShanSQL目录到sys.path
daishan_root = src_root / "DaiShanSQL" / "DaiShanSQL"
if str(daishan_root) not in sys.path:
    sys.path.insert(0, str(daishan_root))


# E2E test configuration
class E2EConfig:
    """E2E test configuration."""

    DEFAULT_TIMEOUT = 30
    HEALTH_CHECK_INTERVAL = 1
    HEALTH_CHECK_MAX_RETRIES = 30
    BASE_URL = "http://127.0.0.1:8000"
    TEST_USER_ID = "test_e2e"


def check_e2e_dependencies() -> list[str]:
    """Check if E2E test dependencies are installed.

    Returns:
        List of missing dependencies
    """
    missing = []

    try:
        import pandas  # noqa: F401
    except ImportError:
        missing.append("pandas")

    try:
        import openpyxl  # noqa: F401
    except ImportError:
        missing.append("openpyxl")

    try:
        import httpx  # noqa: F401
    except ImportError:
        missing.append("httpx")

    return missing


def get_dependency_install_hint() -> str:
    """Get installation hint for missing dependencies."""
    missing = check_e2e_dependencies()
    if not missing:
        return "All E2E dependencies are installed."

    packages = " ".join(missing)
    return f"Missing dependencies: {packages}\nInstall with: uv add --dev {packages}"
