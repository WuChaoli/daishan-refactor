"""
log_manager导入辅助模块
提供统一的导入接口,处理测试环境中的导入降级
"""

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
