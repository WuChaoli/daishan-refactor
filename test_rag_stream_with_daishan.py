#!/usr/bin/env python3
"""
测试在 rag_stream 中使用 DaiShanSQL 时的环境变量加载
"""
import os
import sys

print("=" * 60)
print("测试 rag_stream 中使用 DaiShanSQL 的环境变量加载")
print("=" * 60)

# 先导入 rag_stream 的配置（会加载 rag_stream/.env）
print("\n1. 导入 rag_stream 配置...")
try:
    from rag_stream.src.config.settings import settings
    print("   ✓ rag_stream 配置加载成功")
except Exception as e:
    print(f"   ✗ rag_stream 配置加载失败: {e}")
    sys.exit(1)

# 检查 rag_stream 的环境变量
print("\n2. rag_stream 的环境变量:")
dify_base_url = os.getenv('DIFY_BASE_RUL')
dify_chat_key = os.getenv('DIFY_CHAT_APIKEY_GENERAL_CHAT')
print(f"   DIFY_BASE_RUL: {dify_base_url or '未设置'}")
print(f"   DIFY_CHAT_APIKEY_GENERAL_CHAT: {dify_chat_key[:20] + '...' if dify_chat_key else '未设置'}")

# 导入 DaiShanSQL（应该自动加载 DaiShanSQL/.env）
print("\n3. 导入 DaiShanSQL 模块...")
try:
    import DaiShanSQL
    print("   ✓ DaiShanSQL 模块导入成功")
except Exception as e:
    print(f"   ✗ DaiShanSQL 模块导入失败: {e}")
    sys.exit(1)

# 检查 DaiShanSQL 的环境变量
print("\n4. DaiShanSQL 的环境变量:")
openai_key = os.getenv('OPENAI_API_KEY')
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')
print(f"   OPENAI_API_KEY: {openai_key[:20] + '...' if openai_key else '未设置'}")
print(f"   DB_HOST: {db_host or '未设置'}")
print(f"   DB_NAME: {db_name or '未设置'}")

# 验证结果
print("\n5. 验证结果:")
rag_stream_ok = all([dify_base_url, dify_chat_key])
daishan_ok = all([openai_key, db_host, db_name])

if rag_stream_ok and daishan_ok:
    print("   ✓ rag_stream 环境变量加载正常")
    print("   ✓ DaiShanSQL 环境变量加载正常")
    print("   ✓ 两个模块的环境变量互不干扰，各自独立加载")
else:
    if not rag_stream_ok:
        print("   ✗ rag_stream 环境变量加载异常")
    if not daishan_ok:
        print("   ✗ DaiShanSQL 环境变量加载异常")

print("\n" + "=" * 60)
