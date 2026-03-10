#!/usr/bin/env python3
"""
测试重试机制 - 多次执行观察重试行为
"""

import sys
import time
sys.path.insert(0, '/home/wuchaoli/codespace/daishan-refactor/src')

from rag_stream.config.settings import settings
from rag_stream.utils.ragflow_client import RagflowClient

print("=" * 70)
print("RAGFlow 重试机制测试")
print("场景: 连续多次执行，观察是否触发重试")
print("=" * 70)

# 测试10次连接
success_count = 0
retry_count = 0

for i in range(10):
    print(f"\n测试 #{i+1}/10:")
    client = RagflowClient(
        ragflow_config=settings.ragflow,
        intent_config=settings.intent,
    )

    start = time.time()
    try:
        client._ensure_datasets_loaded()
        elapsed = time.time() - start

        if len(client.datasets) > 0:
            success_count += 1
            print(f"  ✓ 成功 ({elapsed:.2f}s) - {len(client.datasets)} 个数据集")
        else:
            print(f"  ⚠ 无数据 ({elapsed:.2f}s)")
    except Exception as e:
        elapsed = time.time() - start
        print(f"  ✗ 失败 ({elapsed:.2f}s): {type(e).__name__}")

    time.sleep(0.5)  # 短暂间隔

print(f"\n{'=' * 70}")
print(f"统计: {success_count}/10 成功")
print("=" * 70)
