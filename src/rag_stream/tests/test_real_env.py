"""
真实环境测试脚本

使用真实 AI 服务验证端到端链路，覆盖典型企业名改写场景和边界情况。
执行方式：python -m pytest src/rag_stream/tests/test_real_env.py -v
或者：python scripts/test_real_env.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# 添加项目路径
# 当前文件: src/rag_stream/tests/test_real_env.py
# 路径层级: src/rag_stream/tests/ -> src/rag_stream/ -> src/ -> project_root
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent  # 到达项目根目录
src_root = project_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

# 添加 rag_stream/src 到路径以支持相对导入
rag_stream_src = src_root / "rag_stream" / "src"
if str(rag_stream_src) not in sys.path:
    sys.path.insert(0, str(rag_stream_src))

from config.settings import load_settings, QueryChatConfig
from utils.query_chat import rewrite_query


@dataclass
class TestResult:
    """单个测试用例的执行结果"""

    case_id: str
    category: str
    input: str
    output: str
    passed: bool
    duration_ms: float
    error_message: str = ""


@dataclass
class TestReport:
    """测试报告"""

    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    total_duration_ms: float = 0.0
    results: list[TestResult] = field(default_factory=list)

    def add_result(self, result: TestResult) -> None:
        self.results.append(result)
        self.total += 1
        if result.passed:
            self.passed += 1
        else:
            self.failed += 1
        self.total_duration_ms += result.duration_ms


def load_test_cases() -> list[dict[str, Any]]:
    """加载测试用例"""
    test_data_path = Path(__file__).parent / "data" / "real_env_test_cases.json"
    with open(test_data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("test_cases", [])


def validate_result(
    output: str, expected_patterns: dict[str, list[str]], category: str
) -> tuple[bool, str]:
    """
    验证输出结果是否符合预期

    Returns:
        (is_valid, error_message)
    """
    should_not_contain = expected_patterns.get("should_not_contain", [])
    should_contain = expected_patterns.get("should_contain", [])

    # 边界情况特殊处理
    if category == "boundary":
        # 空字符串或纯标点，期望保持原样
        if not should_not_contain and not should_contain:
            return True, ""

    # 检查不应包含的内容
    for pattern in should_not_contain:
        if pattern in output:
            return False, f"输出不应包含 '{pattern}'，但实际包含"

    # 检查应包含的内容（边界情况除外）
    if category != "boundary":
        for pattern in should_contain:
            if pattern not in output:
                return False, f"输出应包含 '{pattern}'，但实际未包含"

    return True, ""


async def run_single_test(
    case: dict[str, Any], config: QueryChatConfig, verbose: bool = False
) -> TestResult:
    """执行单个测试用例"""
    case_id = case["id"]
    category = case["category"]
    input_query = case["input"]
    expected_patterns = case.get("expected_patterns", {})

    if verbose:
        print(f"  执行 {case_id}: {case.get('description', '')}")

    start_time = time.perf_counter()

    try:
        # 执行改写
        output = await asyncio.wait_for(
            rewrite_query(input_query, config), timeout=30.0
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        # 验证结果
        passed, error_message = validate_result(output, expected_patterns, category)

        return TestResult(
            case_id=case_id,
            category=category,
            input=input_query,
            output=output,
            passed=passed,
            duration_ms=duration_ms,
            error_message=error_message,
        )

    except asyncio.TimeoutError:
        duration_ms = (time.perf_counter() - start_time) * 1000
        return TestResult(
            case_id=case_id,
            category=category,
            input=input_query,
            output="",
            passed=False,
            duration_ms=duration_ms,
            error_message="执行超时（>30秒）",
        )
    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        return TestResult(
            case_id=case_id,
            category=category,
            input=input_query,
            output="",
            passed=False,
            duration_ms=duration_ms,
            error_message=f"执行异常: {type(e).__name__}: {e}",
        )


async def run_tests(
    category_filter: str | None = None, verbose: bool = False, dry_run: bool = False
) -> TestReport:
    """
    运行所有测试

    Args:
        category_filter: 只运行指定类别的测试
        verbose: 是否输出详细信息
        dry_run: 是否模拟运行（不调用 AI）

    Returns:
        测试报告
    """
    report = TestReport()

    # 检查是否跳过测试
    if os.getenv("SKIP_REAL_ENV_TEST") == "1":
        print("⚠️  SKIP_REAL_ENV_TEST=1，跳过真实环境测试")
        return report

    # 加载配置
    try:
        settings = load_settings()
        config = settings.query_chat
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")
        return report

    # 检查配置有效性
    if not config.enabled:
        print("⚠️  query_chat 已禁用（enabled=false），跳过测试")
        return report

    if not (config.api_key or "").strip():
        print("⚠️  QUERY_CHAT_API_KEY 未配置，跳过真实环境测试")
        print("   如需运行测试，请设置环境变量或检查 config.yaml")
        return report

    # 加载测试用例
    test_cases = load_test_cases()
    if not test_cases:
        print("❌ 未找到测试用例")
        return report

    # 过滤测试用例
    if category_filter:
        test_cases = [tc for tc in test_cases if tc["category"] == category_filter]
        if not test_cases:
            print(f"⚠️  未找到类别为 '{category_filter}' 的测试用例")
            return report

    print(f"\n🚀 开始运行 {len(test_cases)} 个真实环境测试...")
    if dry_run:
        print("   (模拟模式，不调用 AI)")
    print()

    # 执行测试
    for case in test_cases:
        if dry_run:
            # 模拟模式
            result = TestResult(
                case_id=case["id"],
                category=case["category"],
                input=case["input"],
                output="[DRY RUN] " + case["input"],
                passed=True,
                duration_ms=0.0,
                error_message="",
            )
        else:
            result = await run_single_test(case, config, verbose)

        report.add_result(result)

        # 实时输出结果
        status = "✅" if result.passed else "❌"
        duration_str = f"{result.duration_ms:.0f}ms"
        print(f"  {status} {result.case_id} ({duration_str})")

        if verbose and not result.passed:
            print(f"     输入: {result.input[:50]}...")
            print(f"     输出: {result.output[:50]}...")
            print(f"     错误: {result.error_message}")

    return report


def print_report(report: TestReport) -> None:
    """打印测试报告"""
    print("\n" + "=" * 60)
    print("📊 测试报告")
    print("=" * 60)
    print(f"  总计: {report.total}")
    print(f"  通过: {report.passed}")
    print(f"  失败: {report.failed}")
    print(f"  跳过: {report.skipped}")
    print(f"  总耗时: {report.total_duration_ms:.0f}ms")
    print()

    if report.failed > 0:
        print("❌ 失败的测试用例:")
        for result in report.results:
            if not result.passed:
                print(f"\n  {result.case_id} ({result.category})")
                print(f"    输入: {result.input[:60]}...")
                print(
                    f"    输出: {result.output[:60]}..."
                    if result.output
                    else "    输出: (空)"
                )
                print(f"    错误: {result.error_message}")
        print()


def main(
    category: str | None = None, verbose: bool = False, dry_run: bool = False
) -> int:
    """
    主函数

    Returns:
        0: 所有测试通过
        1: 有测试失败
    """
    try:
        report = asyncio.run(run_tests(category, verbose, dry_run))
        print_report(report)

        if report.failed > 0:
            return 1
        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        return 130
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        return 1


if __name__ == "__main__":
    # 支持命令行参数
    import argparse

    parser = argparse.ArgumentParser(description="真实环境测试")
    parser.add_argument("--category", "-c", help="只运行指定类别的测试")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出模式")
    parser.add_argument(
        "--dry-run", "-d", action="store_true", help="模拟运行（不调用 AI）"
    )

    args = parser.parse_args()
    exit_code = main(category=args.category, verbose=args.verbose, dry_run=args.dry_run)
    sys.exit(exit_code)
