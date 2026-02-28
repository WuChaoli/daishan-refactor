#!/usr/bin/env python3
"""
真实环境测试 - 命令行入口

提供便捷的命令行方式运行真实环境测试。

Usage:
    python scripts/test_real_env.py
    python scripts/test_real_env.py --verbose
    python scripts/test_real_env.py --category typical_company
    python scripts/test_real_env.py --list
    python scripts/test_real_env.py --dry-run

Environment Variables:
    SKIP_REAL_ENV_TEST: 设置为1跳过测试
    QUERY_CHAT_API_KEY: AI服务API密钥（覆盖配置文件）
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def setup_paths():
    """设置Python路径"""
    # 获取项目根目录
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent

    # 添加 src/rag_stream/src 到路径（用于导入 config, utils 等）
    rag_stream_src = project_root / "src" / "rag_stream" / "src"
    if str(rag_stream_src) not in sys.path:
        sys.path.insert(0, str(rag_stream_src))

    # 添加 src/rag_stream 到路径（用于导入 tests 模块）
    rag_stream_root = project_root / "src" / "rag_stream"
    if str(rag_stream_root) not in sys.path:
        sys.path.insert(0, str(rag_stream_root))

    return project_root


def check_environment():
    """检查环境配置"""
    api_key = os.getenv("QUERY_CHAT_API_KEY")

    if not api_key:
        print("⚠️  警告: QUERY_CHAT_API_KEY 环境变量未设置")
        print("   测试将尝试从配置文件加载")
        print()
        return False

    return True


def list_test_cases():
    """列出所有测试用例"""
    setup_paths()

    from tests.test_real_env import load_test_cases

    test_cases = load_test_cases()

    print("\n📋 测试用例列表")
    print("=" * 60)

    current_category = None
    for case in test_cases:
        category = case["category"]
        if category != current_category:
            current_category = category
            print(f"\n【{category}】")

        print(f"  {case['id']}: {case['description']}")
        print(
            f"    输入: {case['input'][:50]}{'...' if len(case['input']) > 50 else ''}"
        )

    print(f"\n总计: {len(test_cases)} 个测试用例")
    print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="真实环境测试 - 验证 AI 改写功能",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/test_real_env.py              # 运行所有测试
  python scripts/test_real_env.py -v           # 详细输出
  python scripts/test_real_env.py -c typical_company   # 只运行指定类别
  python scripts/test_real_env.py --list       # 列出测试用例
  python scripts/test_real_env.py --dry-run    # 模拟运行
        """,
    )

    parser.add_argument(
        "--category",
        "-c",
        help="只运行指定类别的测试 (typical_company, complex_structure, no_company, boundary)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出模式")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有测试用例")
    parser.add_argument(
        "--dry-run", "-d", action="store_true", help="模拟运行（不调用 AI）"
    )

    args = parser.parse_args()

    # 列出测试用例
    if args.list:
        list_test_cases()
        return 0

    # 设置路径
    setup_paths()

    # 检查环境
    if not args.dry_run:
        check_environment()

    # 导入并运行测试
    try:
        from tests.test_real_env import main as run_tests

        exit_code = run_tests(
            category=args.category, verbose=args.verbose, dry_run=args.dry_run
        )
        return exit_code

    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("   请确保从项目根目录运行此脚本")
        return 1
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
