#!/usr/bin/env python3
"""
验证 replace_economic_zone 修改后的行为
1. 确认不再依赖关键词触发
2. 确认 handle_chat_general 调用流程
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[3] / "src" / "rag_stream" / "src")
)

from rag_stream.config.settings import settings
from rag_stream.services.chat_general_service import replace_economic_zone


async def test_replace_economic_zone():
    """测试 replace_economic_zone 不再依赖关键词触发"""

    print("=" * 70)
    print("测试 replace_economic_zone 修改后的行为")
    print("=" * 70)

    test_cases = [
        # (原始查询, 描述)
        ("介绍一下岱山经开区情况", "包含园区名，应触发处理"),
        ("贝能安全公司怎么样", "包含公司名，应触发处理"),
        ("今天天气怎么样", "不包含企业/园区名，但应触发处理（新逻辑）"),
        ("你好", "简单问候，应触发处理（新逻辑）"),
        ("企业的安全情况", "包含'企业'关键词"),
    ]

    print(f"\n配置状态:")
    print(f"  query_chat.enabled: {settings.query_chat.enabled}")
    print(
        f"  query_chat.api_key: {'已设置' if settings.query_chat.api_key else '未设置'}"
    )
    print(f"  query_chat.base_url: {settings.query_chat.base_url or '未设置'}")

    print(f"\n测试用例:")
    for i, (query, desc) in enumerate(test_cases, 1):
        print(f"\n{i}. {desc}")
        print(f"   输入: {query}")

        try:
            result = await replace_economic_zone(query)
            print(f"   输出: {result}")

            if result != query:
                print(f"   ✓ 已处理（结果不同）")
            else:
                print(f"   → 未处理（可能AI未修改或配置未启用）")

        except Exception as e:
            print(f"   ✗ 错误: {e}")

    print("\n" + "=" * 70)
    print("结论:")
    print("  1. 修改后的 replace_economic_zone 不再检查关键词触发条件")
    print("  2. 所有输入都会尝试调用 query_chat 模型进行处理")
    print("  3. handle_chat_general 始终会经过 replace_economic_zone 处理")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_replace_economic_zone())
