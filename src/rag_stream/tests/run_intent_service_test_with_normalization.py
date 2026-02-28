#!/usr/bin/env python3
"""
意图分类准确性测试（完整流程版本）
包含关键词删除 -> 意图判断的完整链路
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

# 添加项目路径
sys.path.insert(
    0, str(Path(__file__).resolve().parents[3] / "src" / "rag_stream" / "src")
)

from rag_stream.config.settings import settings
from rag_stream.utils.ragflow_client import RagflowClient
from rag_stream.services.intent_service.intent_service import IntentService
from rag_stream.services.chat_general_service import replace_economic_zone


async def test_intent_service_with_normalization():
    """测试完整流程：关键词删除 -> 意图分类"""

    print("=" * 70)
    print("意图分类准确性测试（包含关键词删除流程）")
    print("=" * 70)

    # 读取测试数据
    test_data_path = (
        Path(__file__).resolve().parents[3]
        / "src"
        / "rag_stream"
        / "tests"
        / "data"
        / "intent_test_cases.xlsx"
    )
    df = pd.read_excel(test_data_path)

    total_cases = len(df)
    print(f"\n总测试用例数: {total_cases}")
    print(f"类型分布:")
    print(df["expected_type"].value_counts().sort_index())

    # 初始化服务
    print("\n初始化 IntentService...")
    try:
        ragflow_client = RagflowClient(
            ragflow_config=settings.ragflow, intent_config=settings.intent
        )
        intent_service = IntentService(ragflow_client=ragflow_client)
        print("✓ IntentService 初始化成功")
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        return None

    # 运行测试（完整流程）
    print("\n开始测试（完整流程：关键词删除 -> 意图判断）...")
    print("-" * 70)

    results = []
    correct_count = 0
    type_stats = {
        1: {"total": 0, "correct": 0},
        2: {"total": 0, "correct": 0},
        3: {"total": 0, "correct": 0},
    }

    for idx, row in df.iterrows():
        original_query = row["question"]
        expected_type = int(row["expected_type"])

        try:
            # 步骤1：关键词删除（完整流程的关键）
            normalized_query = await replace_economic_zone(original_query)

            # 步骤2：使用删除后的 query 进行意图识别
            result = await intent_service.process_query(
                normalized_query, user_id="test_user"
            )
            actual_type = result.get("type", settings.intent.default_type)

            is_correct = actual_type == expected_type
            if is_correct:
                correct_count += 1
                type_stats[expected_type]["correct"] += 1

            type_stats[expected_type]["total"] += 1

            results.append(
                {
                    "original_query": original_query,
                    "normalized_query": normalized_query,
                    "expected_type": expected_type,
                    "actual_type": actual_type,
                    "correct": is_correct,
                    "similarity": result.get("similarity", 0.0),
                    "database": result.get("database", ""),
                    "question": result.get("question", ""),
                }
            )

            status = "✓" if is_correct else "✗"
            changed = "（已删除）" if normalized_query != original_query else "（未变）"
            print(
                f"{status} [{idx + 1}/{total_cases}] Type {expected_type} -> {actual_type} {changed}"
            )
            print(f"   原: {original_query[:50]}...")
            print(f"   删: {normalized_query[:50]}...")
            print()

        except Exception as e:
            print(f"✗ [{idx + 1}/{total_cases}] Error: {e}")
            print(f"   原: {original_query[:50]}...")
            results.append(
                {
                    "original_query": original_query,
                    "normalized_query": f"ERROR: {e}",
                    "expected_type": expected_type,
                    "actual_type": f"ERROR",
                    "correct": False,
                    "similarity": 0.0,
                    "database": "",
                    "question": "",
                }
            )
            type_stats[expected_type]["total"] += 1

    # 计算统计信息
    accuracy = correct_count / total_cases if total_cases > 0 else 0

    print("=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    print(f"总用例数: {total_cases}")
    print(f"正确数: {correct_count}")
    print(f"错误数: {total_cases - correct_count}")
    print(f"总体正确率: {accuracy:.2%}")
    print("\n各类型正确率:")
    for t in [1, 2, 3]:
        stats = type_stats[t]
        if stats["total"] > 0:
            type_accuracy = stats["correct"] / stats["total"]
            print(
                f"  Type {t}: {stats['correct']}/{stats['total']} ({type_accuracy:.2%})"
            )

    # 保存详细结果
    output_dir = (
        Path(__file__).resolve().parents[4]
        / ".planning"
        / "quick"
        / "002-retest-intent-with-normalization"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    # 生成 Markdown 报告
    report_path = output_dir / "intent_classification_report_with_normalization.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 意图分类准确性测试报告（含关键词删除）\n\n")
        f.write(f"**测试时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(
            f"**测试流程:** 关键词删除（replace_economic_zone）→ 意图识别（IntentService）\n\n"
        )

        f.write("## 测试概览\n\n")
        f.write(f"- **总测试用例数:** {total_cases}\n")
        f.write(f"- **正确分类数:** {correct_count}\n")
        f.write(f"- **错误分类数:** {total_cases - correct_count}\n")
        f.write(f"- **总体正确率:** {accuracy:.2%}\n\n")

        f.write("## 各类型正确率统计\n\n")
        f.write("| 意图类型 | 测试数 | 正确数 | 正确率 |\n")
        f.write("|---------|-------|-------|--------|\n")
        for t in [1, 2, 3]:
            stats = type_stats[t]
            if stats["total"] > 0:
                type_accuracy = stats["correct"] / stats["total"]
                f.write(
                    f"| Type {t} | {stats['total']} | {stats['correct']} | {type_accuracy:.2%} |\n"
                )
        f.write("\n")

        f.write("## 错误分类详细列表\n\n")
        f.write("| # | 原查询 | 删除后 | 期望 | 实际 | 相似度 |\n")
        f.write("|---|-------|--------|-----|-----|-------|\n")
        error_count = 0
        for idx, r in enumerate(results):
            if not r["correct"]:
                error_count += 1
                orig_short = (
                    r["original_query"][:40] + "..."
                    if len(r["original_query"]) > 40
                    else r["original_query"]
                )
                norm_short = (
                    str(r["normalized_query"])[:40] + "..."
                    if len(str(r["normalized_query"])) > 40
                    else str(r["normalized_query"])
                )
                f.write(
                    f"| {error_count} | {orig_short} | {norm_short} | {r['expected_type']} | {r['actual_type']} | {r['similarity']:.3f} |\n"
                )

        if error_count == 0:
            f.write("\n✓ 所有测试用例均正确分类！\n")

        f.write("\n## 对比分析\n\n")
        f.write("### 与未删除版本对比\n\n")
        f.write("| 版本 | 总体正确率 | Type 1 | Type 2 | Type 3 |\n")
        f.write("|-----|-----------|--------|--------|--------|\n")
        f.write("| 无删除 | 54.55% | 0.00% | 66.67% | 60.87% |\n")
        type1_acc = (
            type_stats[1]["correct"] / type_stats[1]["total"]
            if type_stats[1]["total"] > 0
            else 0
        )
        type2_acc = (
            type_stats[2]["correct"] / type_stats[2]["total"]
            if type_stats[2]["total"] > 0
            else 0
        )
        type3_acc = (
            type_stats[3]["correct"] / type_stats[3]["total"]
            if type_stats[3]["total"] > 0
            else 0
        )
        f.write(
            f"| 有删除 | {accuracy:.2%} | {type1_acc:.2%} | {type2_acc:.2%} | {type3_acc:.2%} |\n"
        )

        f.write("\n## 测试结论\n\n")
        if accuracy >= 0.9:
            f.write("**结论:** 意图分类准确性优秀（≥90%），完整流程有效。\n")
        elif accuracy >= 0.7:
            f.write("**结论:** 意图分类准确性良好（≥70%），仍有优化空间。\n")
        else:
            f.write(
                "**结论:** 意图分类准确性需要改进（<70%），建议优化知识库或调整阈值。\n"
            )

        f.write("\n## 观察\n\n")
        f.write("### 关键词删除效果\n\n")
        changed_count = sum(
            1 for r in results if r["original_query"] != r["normalized_query"]
        )
        f.write(
            f"- 发生变化的查询: {changed_count}/{total_cases} ({changed_count / total_cases * 100:.1f}%)\n"
        )

        f.write("\n### 改进建议\n\n")
        if (
            type_stats[1]["total"] > 0
            and type_stats[1]["correct"] / type_stats[1]["total"] < 0.8
        ):
            f.write("- Type 1（指令集类型）分类准确率较低\n")
        if (
            type_stats[2]["total"] > 0
            and type_stats[2]["correct"] / type_stats[2]["total"] < 0.8
        ):
            f.write("- Type 2（数据库问题）分类准确率较低\n")
        if (
            type_stats[3]["total"] > 0
            and type_stats[3]["correct"] / type_stats[3]["total"] < 0.8
        ):
            f.write("- Type 3（固定问题）分类准确率较低\n")

    print(f"\n✓ 测试报告已保存: {report_path}")

    # 同时保存 JSON 格式结果
    json_path = output_dir / "test_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "flow": "normalization_then_intent",
                "total_cases": total_cases,
                "correct_count": correct_count,
                "accuracy": accuracy,
                "type_stats": type_stats,
                "results": results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"✓ 详细结果已保存: {json_path}")

    return {
        "total": total_cases,
        "correct": correct_count,
        "accuracy": accuracy,
        "type_stats": type_stats,
    }


if __name__ == "__main__":
    result = asyncio.run(test_intent_service_with_normalization())
    if result:
        print("\n测试完成!")
        sys.exit(0)
    else:
        print("\n测试失败!")
        sys.exit(1)
