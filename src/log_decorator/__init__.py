"""日志装饰器包

提供统一的函数日志记录装饰器，支持：
- 自动记录入参、出参、耗时
- 智能解析复杂对象
- 双日志文件（全局+功能级）
- 配置化日志行为

使用示例:

    def my_function(x, y):
        return x + y
"""
from .decorator import log, log_entry, log_end, logger, logging
from .parser import parse_obj
from .config import load_config

__version__ = "1.0.0"
__all__ = ["log", "log_entry", "log_end", "logger", "logging", "parse_obj", "load_config"]
