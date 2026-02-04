#!/usr/bin/env python3
"""
测试 DaiShanSQL 模块是否自动加载 .env 文件
"""
import os
import sys

print("=" * 60)
print("测试 DaiShanSQL .env 自动加载")
print("=" * 60)

# 在导入前检查环境变量
print("\n1. 导入 DaiShanSQL 之前的环境变量状态:")
print(f"   OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', '未设置')}")
print(f"   DB_HOST: {os.getenv('DB_HOST', '未设置')}")
print(f"   DB_NAME: {os.getenv('DB_NAME', '未设置')}")

# 导入 DaiShanSQL 模块
print("\n2. 正在导入 DaiShanSQL 模块...")
try:
    import DaiShanSQL
    print("   ✓ DaiShanSQL 模块导入成功")
except Exception as e:
    print(f"   ✗ DaiShanSQL 模块导入失败: {e}")
    sys.exit(1)

# 导入后检查环境变量
print("\n3. 导入 DaiShanSQL 之后的环境变量状态:")
openai_key = os.getenv('OPENAI_API_KEY')
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
openai_model = os.getenv('OPENAI_MODEL')

print(f"   OPENAI_API_KEY: {openai_key[:20] + '...' if openai_key else '未设置'}")
print(f"   OPENAI_MODEL: {openai_model or '未设置'}")
print(f"   DB_HOST: {db_host or '未设置'}")
print(f"   DB_NAME: {db_name or '未设置'}")
print(f"   DB_USER: {db_user or '未设置'}")

# 验证结果
print("\n4. 验证结果:")
all_loaded = all([openai_key, db_host, db_name, db_user, openai_model])

if all_loaded:
    print("   ✓ 所有测试的环境变量都已成功加载")
    print("   ✓ DaiShanSQL .env 文件自动加载功能正常")
else:
    print("   ✗ 部分环境变量未加载")
    print("   ✗ DaiShanSQL .env 文件自动加载功能异常")

print("\n" + "=" * 60)
