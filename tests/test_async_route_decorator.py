"""回归测试：@log 装饰后异步函数语义不应丢失。"""

import asyncio
import inspect
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from log_decorator import log


def test_log_decorator_should_keep_async_function_async():
    @log()
    async def health():
        return {"ok": True}

    assert inspect.iscoroutinefunction(health) is True
    assert asyncio.run(health()) == {"ok": True}
