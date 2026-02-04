"""
测试函数追踪器
"""

import asyncio
from rag_stream.src.utils.function_tracer import trace_function


@trace_function
async def test_async_function(name: str, age: int) -> dict:
    """测试异步函数"""
    await asyncio.sleep(0.1)
    return {"name": name, "age": age, "status": "success"}


@trace_function
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

    print("\n追踪日志已写入: rag_stream/logs/function_trace.log")
    print("请查看该文件以验证追踪功能")


if __name__ == "__main__":
    asyncio.run(main())
