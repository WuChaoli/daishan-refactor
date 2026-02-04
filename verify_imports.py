#!/usr/bin/env python3
"""
验证 DaiShanSQL 包导入是否正常工作
"""

print("=" * 60)
print("验证 DaiShanSQL 包导入")
print("=" * 60)

# 测试 1: 导入主类
print("\n1. 测试导入主类...")
try:
    from DaiShanSQL import Server, SQLAgent, MySQLManager, SQLFixed
    print("   ✓ 成功导入: Server, SQLAgent, MySQLManager, SQLFixed")
except ImportError as e:
    print(f"   ✗ 导入失败: {e}")
    exit(1)

# 测试 2: 创建 Server 实例
print("\n2. 测试创建 Server 实例...")
try:
    server = Server()
    print(f"   ✓ 成功创建 Server 实例: {server}")
except Exception as e:
    print(f"   ✗ 创建失败: {e}")
    exit(1)

# 测试 3: 检查版本
print("\n3. 检查包版本...")
try:
    import DaiShanSQL
    version = getattr(DaiShanSQL, '__version__', 'unknown')
    print(f"   ✓ DaiShanSQL 版本: {version}")
except Exception as e:
    print(f"   ✗ 版本检查失败: {e}")

# 测试 4: 在 rag_stream 中导入
print("\n4. 测试在 rag_stream 服务中导入...")
try:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rag_stream'))
    from src.services.source_dispath_srvice import handle_source_dispatch
    print("   ✓ 成功从 rag_stream 导入 handle_source_dispatch")
except ImportError as e:
    print(f"   ✗ 导入失败: {e}")
    exit(1)

print("\n" + "=" * 60)
print("所有导入测试通过！")
print("=" * 60)
