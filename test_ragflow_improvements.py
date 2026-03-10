#!/usr/bin/env python3
"""
验证 RAGFlow 连接优化是否生效
"""

import sys
sys.path.insert(0, '/home/wuchaoli/codespace/daishan-refactor/src')

from rag_stream.config.settings import settings
from rag_stream.utils.ragflow_client import RagflowClient

print("=" * 60)
print("RAGFlow 连接优化验证")
print("=" * 60)

# 1. 验证配置
print("\n1. 配置验证:")
print(f"   max_retries: {settings.ragflow.max_retries}")
print(f"   retry_delay: {settings.ragflow.retry_delay}")
print(f"   retry_backoff_factor: {settings.ragflow.retry_backoff_factor}")
print(f"   retry_max_delay: {settings.ragflow.retry_max_delay}")
print(f"   list_datasets_page_size: {settings.ragflow.list_datasets_page_size}")
print(f"   list_datasets_timeout: {settings.ragflow.list_datasets_timeout}")

# 2. 验证客户端初始化
print("\n2. 客户端初始化:")
try:
    client = RagflowClient(
        ragflow_config=settings.ragflow,
        intent_config=settings.intent,
    )
    print("   ✓ RagflowClient 初始化成功")
except Exception as e:
    print(f"   ✗ 初始化失败: {e}")
    sys.exit(1)

# 3. 测试连接
print("\n3. 连接测试:")
try:
    result = client.test_connection()
    print(f"   ✓ 连接测试结果: {'成功' if result else '失败'}")
except Exception as e:
    print(f"   ✗ 连接测试异常: {e}")

# 4. 验证数据集加载
print("\n4. 数据集加载:")
try:
    client._ensure_datasets_loaded()
    print(f"   ✓ 数据集数量: {len(client.datasets)}")
    print(f"   ✓ 数据集映射: {list(client.dataset_map.keys())}")
except Exception as e:
    print(f"   ✗ 数据集加载异常: {e}")

print("\n" + "=" * 60)
print("验证完成")
print("=" * 60)
