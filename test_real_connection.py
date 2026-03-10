#!/usr/bin/env python3
"""
RAGFlow 真实连接测试 - 模拟服务启动过程
"""

import sys
import time
sys.path.insert(0, '/home/wuchaoli/codespace/daishan-refactor/src')

print("=" * 70)
print("RAGFlow 真实连接测试")
print("测试场景: 模拟服务启动时的 RAGFlow 连接检查")
print("=" * 70)

# 1. 加载配置
print("\n[1/4] 加载配置...")
from rag_stream.config.settings import settings
print(f"  ✓ RAGFlow Base URL: {settings.ragflow.base_url}")
print(f"  ✓ 重试配置: max_retries={settings.ragflow.max_retries}, "
      f"delay={settings.ragflow.retry_delay}s, backoff={settings.ragflow.retry_backoff_factor}")

# 2. 初始化客户端
print("\n[2/4] 初始化 RagflowClient...")
from rag_stream.utils.ragflow_client import RagflowClient

start = time.time()
client = RagflowClient(
    ragflow_config=settings.ragflow,
    intent_config=settings.intent,
)
print(f"  ✓ 初始化完成 ({time.time() - start:.2f}s)")

# 3. 测试连接（带重试）
print("\n[3/4] 测试 RAGFlow 连接（带重试机制）...")
print("  开始连接测试，若失败将自动重试...")
start = time.time()
try:
    result = client.test_connection()
    elapsed = time.time() - start
    print(f"  ✓ 连接测试完成 ({elapsed:.2f}s)")
    print(f"  ✓ 服务可用: {result}")
except Exception as e:
    elapsed = time.time() - start
    print(f"  ✗ 连接测试失败 ({elapsed:.2f}s): {e}")

# 4. 加载数据集（真实场景）
print("\n[4/4] 加载数据集（模拟首次查询）...")
print("  调用 _ensure_datasets_loaded()...")
start = time.time()
try:
    client._ensure_datasets_loaded()
    elapsed = time.time() - start
    print(f"  ✓ 数据集加载完成 ({elapsed:.2f}s)")
    print(f"  ✓ 找到 {len(client.datasets)} 个数据集:")
    for ds in client.datasets:
        print(f"    - {ds.name} (ID: {ds.id[:8]}...)")
except Exception as e:
    elapsed = time.time() - start
    print(f"  ✗ 数据集加载失败 ({elapsed:.2f}s): {e}")

# 5. 模拟查询（可选）
print("\n[5/5] 模拟单库查询...")
if client.dataset_map:
    db_name = list(client.dataset_map.keys())[0]
    print(f"  查询数据库: {db_name}")
    start = time.time()
    try:
        import asyncio
        results = asyncio.run(client.query_single_database("测试查询", db_name))
        elapsed = time.time() - start
        print(f"  ✓ 查询完成 ({elapsed:.2f}s), 返回 {len(results)} 条结果")
    except Exception as e:
        elapsed = time.time() - start
        print(f"  ✗ 查询失败 ({elapsed:.2f}s): {e}")
else:
    print("  跳过（无可用数据集）")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
