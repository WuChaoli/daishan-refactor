"""
log_manager导入辅助模块
提供统一的导入接口,处理测试环境中的导入降级
"""
import sys
import os
from pathlib import Path

# 确保项目根目录的src在sys.path中
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent.parent  # 向上5级到项目根目录
src_root = project_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

try:
    from log_manager import trace, marker, entry_trace
    __all__ = ["trace", "marker", "entry_trace"]
except ImportError:
    # 测试环境降级: 使用空的装饰器
    def trace(func):
        """降级trace装饰器"""
        return func

    def marker(name: str, data: dict = None, level: str = "INFO"):
        """降级marker函数"""
        pass

    def entry_trace(name: str):
        """降级entry_trace装饰器"""
        def decorator(func):
            return func
        return decorator

    __all__ = ["trace", "marker", "entry_trace"]
