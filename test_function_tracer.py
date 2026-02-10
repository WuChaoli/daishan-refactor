"""
测试函数追踪器
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src" / "rag_stream"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from log_decorator import log


@log()
async def test_async_function(name: str, age: int) -> dict:
    """测试异步函数"""
    await asyncio.sleep(0.1)
    return {"name": name, "age": age, "status": "success"}


@log()
def test_sync_function(x: int, y: int) -> int:
    """测试同步函数"""
    return x + y


async def main():
    print("开始测试函数追踪器...")

    # 测试异步函数
    result1 = await test_async_function("张三", 25)
    print(f"异步函数结果: {result1}")

    # 测试同步函数
    result2 = test_sync_function(10, 20)
    print(f"同步函数结果: {result2}")

    print("\n追踪日志已写入: src/rag_stream/logs/")
    print("请查看该文件以验证追踪功能")


if __name__ == "__main__":
    asyncio.run(main())
