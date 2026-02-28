"""
意图分类准确性测试脚本
读取 intent_test_cases.xlsx 运行测试并生成报告
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from rag_stream.utils.intent_classifier import (
    IntentClassifier,
    ClassificationResult,
)
from rag_stream.config.settings import IntentClassificationConfig


class IntentClassificationAccuracyTester:
    """意图分类准确性测试器"""

    def __init__(self, config: IntentClassificationConfig):
        self.config = config
        self.classifier = IntentClassifier(config)
        self.test_results: list[dict[str, Any]] = []
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None

    def load_test_cases(self, excel_path: Path) -> list[dict[str, Any]]:
        """从 Excel 文件加载测试用例"""
        df = pd.read_excel(excel_path)
        test_cases = []
        for _, row in df.iterrows():
            test_cases.append(
                {
                    "question": str(row["question"]),
                    "expected_type": int(row["expected_type"]),
                    "description": str(row.get("description", ""))
                    if pd.notna(row.get("description"))
                    else "",
                    "notes": str(row.get("notes", ""))
                    if pd.notna(row.get("notes"))
                    else "",
                }
            )
        return test_cases

    def classify_single(self, question: str) -> ClassificationResult:
        """对单个问题进行分类"""
        return self.classifier.classify(question)

    async def run_tests(self, test_cases: list[dict[str, Any]]) -> None:
        """运行所有测试用例"""
        self.start_time = datetime.now()
        total = len(test_cases)

        print(f"\n{'=' * 80}")
        print(f"开始意图分类准确性测试")
        print(f"{'=' * 80}")
        print(f"总测试用例数: {total}")
        print(f"配置状态: enabled={self.config.enabled}")
        print(f"{'=' * 80}\n")

        for i, case in enumerate(test_cases, 1):
            print(f"[{i}/{total}] 测试: {case['question'][:40]}...")

            result = self.classifier.classify(case["question"])

            test_result = {
                "index": i,
                "question": case["question"],
                "expected_type": case["expected_type"],
                "actual_type": result.type_id,
                "confidence": result.confidence,
                "is_correct": result.type_id == case["expected_type"],
                "is_degraded": result.degraded,
                "raw_response": result.raw_response,
                "notes": case["notes"],
            }
            self.test_results.append(test_result)

            status = "✓" if test_result["is_correct"] else "✗"
            print(
                f"  {status} 期望={case['expected_type']}, 实际={result.type_id}, 置信度={result.confidence:.2f}"
            )

        self.end_time = datetime.now()

    def generate_report(self) -> dict[str, Any]:
        """生成测试报告数据"""
        total = len(self.test_results)
        correct = sum(1 for r in self.test_results if r["is_correct"])
        failed = total - correct
        degraded = sum(1 for r in self.test_results if r["is_degraded"])

        accuracy = (correct / total * 100) if total > 0 else 0

        # 按类型统计
        type_stats = {}
        for type_id in [1, 2, 3]:
            type_cases = [r for r in self.test_results if r["expected_type"] == type_id]
            if type_cases:
                type_correct = sum(1 for r in type_cases if r["is_correct"])
                type_stats[type_id] = {
                    "total": len(type_cases),
                    "correct": type_correct,
                    "accuracy": (type_correct / len(type_cases) * 100),
                }

        # 错误用例
        failed_cases = [r for r in self.test_results if not r["is_correct"]]

        duration = (
            (self.end_time - self.start_time).total_seconds()
            if self.end_time and self.start_time
            else 0
        )

        return {
            "summary": {
                "total_tests": total,
                "correct": correct,
                "failed": failed,
                "degraded": degraded,
                "accuracy": accuracy,
                "duration_seconds": duration,
                "start_time": self.start_time.isoformat() if self.start_time else "",
                "end_time": self.end_time.isoformat() if self.end_time else "",
            },
            "type_statistics": type_stats,
            "failed_cases": failed_cases,
            "all_results": self.test_results,
        }

    def print_report(self, report: dict[str, Any]) -> None:
        """打印测试报告到控制台"""
        summary = report["summary"]
        type_stats = report["type_statistics"]
        failed_cases = report["failed_cases"]

        print(f"\n{'=' * 80}")
        print("测试报告")
        print(f"{'=' * 80}")

        print(f"\n【总体统计】")
        print(f"  总测试数: {summary['total_tests']}")
        print(f"  正确数: {summary['correct']}")
        print(f"  错误数: {summary['failed']}")
        print(f"  降级数: {summary['degraded']}")
        print(f"  正确率: {summary['accuracy']:.2f}%")
        print(f"  耗时: {summary['duration_seconds']:.2f}秒")

        print(f"\n【按类型统计】")
        type_names = {1: "岱山-指令集", 2: "岱山-数据库问题", 3: "岱山-指令集-固定问题"}
        for type_id, stats in sorted(type_stats.items()):
            name = type_names.get(type_id, f"类型{type_id}")
            print(f"  {name}:")
            print(
                f"    测试数: {stats['total']}, 正确数: {stats['correct']}, 正确率: {stats['accuracy']:.2f}%"
            )

        if failed_cases:
            print(f"\n【错误用例详情】({len(failed_cases)}个)")
            for case in failed_cases:
                print(f"\n  [{case['index']}] {case['question']}")
                print(
                    f"      期望类型: {case['expected_type']}, 实际类型: {case['actual_type']}"
                )
                if case["is_degraded"]:
                    print(f"      ⚠ 发生降级")

    def save_report(self, report: dict[str, Any], output_path: Path) -> None:
        """保存测试报告到 JSON 文件"""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n详细报告已保存: {output_path}")

    def generate_markdown_report(self, report: dict[str, Any]) -> str:
        """生成 Markdown 格式报告"""
        summary = report["summary"]
        type_stats = report["type_statistics"]
        failed_cases = report["failed_cases"]

        type_names = {1: "岱山-指令集", 2: "岱山-数据库问题", 3: "岱山-指令集-固定问题"}

        md = f"""# 意图分类准确性测试报告

## 测试概述

| 项目 | 数值 |
|------|------|
| 测试时间 | {self.start_time.strftime("%Y-%m-%d %H:%M:%S") if self.start_time else "-"} |
| 总测试数 | {summary["total_tests"]} |
| 正确数 | {summary["correct"]} |
| 错误数 | {summary["failed"]} |
| 降级数 | {summary["degraded"]} |
| **总体正确率** | **{summary["accuracy"]:.2f}%** |
| 测试耗时 | {summary["duration_seconds"]:.2f}秒 |

## 按类型统计

| 意图类型 | 测试数 | 正确数 | 正确率 |
|----------|--------|--------|--------|
"""
        for type_id in sorted(type_stats.keys()):
            stats = type_stats[type_id]
            name = type_names.get(type_id, f"类型{type_id}")
            md += f"| {name} | {stats['total']} | {stats['correct']} | {stats['accuracy']:.2f}% |\n"

        md += f"""
## 错误用例详情

共 {len(failed_cases)} 个错误用例：

| 序号 | 问题文本 | 期望类型 | 实际类型 | 备注 |
|------|----------|----------|----------|------|
"""
        for case in failed_cases:
            expected_name = type_names.get(
                case["expected_type"], f"类型{case['expected_type']}"
            )
            actual_name = type_names.get(
                case["actual_type"], f"类型{case['actual_type']}"
            )
            note = "降级" if case["is_degraded"] else ""
            question = (
                case["question"][:50] + "..."
                if len(case["question"]) > 50
                else case["question"]
            )
            md += f"| {case['index']} | {question} | {expected_name} | {actual_name} | {note} |\n"

        md += """
## 测试配置

```yaml
"""
        md += f"enabled: {self.config.enabled}\n"
        md += f"model: {self.config.model}\n"
        md += f"timeout: {self.config.timeout}\n"
        md += f"temperature: {self.config.temperature}\n"
        md += """```

## 结论

"""
        if summary["accuracy"] >= 90:
            md += f"✅ **测试结果优秀** - 正确率达到 {summary['accuracy']:.2f}%，意图分类器表现良好。\n"
        elif summary["accuracy"] >= 70:
            md += f"⚠️ **测试结果可接受** - 正确率为 {summary['accuracy']:.2f}%，建议进一步优化。\n"
        else:
            md += f"❌ **测试结果需改进** - 正确率仅 {summary['accuracy']:.2f}%，需要检查分类器配置和模型。\n"

        return md

    def save_markdown_report(self, report: dict[str, Any], output_path: Path) -> None:
        """保存 Markdown 报告"""
        md_content = self.generate_markdown_report(report)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"Markdown 报告已保存: {output_path}")


async def main():
    """主函数"""
    # 配置
    config = IntentClassificationConfig(
        enabled=True,
        api_key="",
        base_url="",
        model="",
        timeout=3,
        temperature=0.0,
        confidence_threshold=0.5,
    )

    # 路径
    excel_path = Path(__file__).parent.parent / "data" / "intent_test_cases.xlsx"
    json_output_path = (
        Path(__file__).parent.parent
        / "data"
        / "intent_classification_test_results.json"
    )
    md_output_path = (
        Path(__file__).parent.parent.parent.parent.parent
        / ".planning"
        / "quick"
        / "001-retest-intent-classification-accuracy"
        / "intent_classification_report.md"
    )

    # 确保输出目录存在
    md_output_path.parent.mkdir(parents=True, exist_ok=True)

    # 创建测试器
    tester = IntentClassificationAccuracyTester(config)

    # 加载测试用例
    print(f"加载测试数据: {excel_path}")
    test_cases = tester.load_test_cases(excel_path)
    print(f"成功加载 {len(test_cases)} 个测试用例")

    # 运行测试
    await tester.run_tests(test_cases)

    # 生成报告
    report = tester.generate_report()

    # 打印报告
    tester.print_report(report)

    # 保存报告
    tester.save_report(report, json_output_path)
    tester.save_markdown_report(report, md_output_path)

    print(f"\n{'=' * 80}")
    print("测试完成")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    asyncio.run(main())
