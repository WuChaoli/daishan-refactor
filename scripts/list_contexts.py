#!/usr/bin/env python3
"""
列出活跃和已归档的开发上下文

用法:
    python scripts/list_contexts.py           # 仅列出活跃上下文
    python scripts/list_contexts.py --all     # 列出所有上下文

示例:
    python scripts/list_contexts.py
    python scripts/list_contexts.py --all
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime


def find_project_root():
    """查找项目根目录（包含 docs/contexts/ 的目录）"""
    current = Path.cwd()
    while current != current.parent:
        if (current / "docs" / "contexts").exists():
            return current
        current = current.parent
    raise FileNotFoundError("无法找到项目根目录（未找到 docs/contexts/ 目录）")


def format_datetime(iso_string: str) -> str:
    """格式化 ISO 时间字符串"""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return iso_string


def print_contexts(contexts: list, title: str):
    """打印上下文列表"""
    if not contexts:
        print(f"\n{title}: 无")
        return

    print(f"\n{title}:")
    print()
    print(f"{'Context ID':<35} {'标题':<20} {'负责人':<15} {'状态':<12} {'最后更新':<16}")
    print("-" * 110)

    for ctx in contexts:
        context_id = ctx.get("contextId", "")
        title = ctx.get("title", "")
        assignee = ctx.get("assignee", "")
        status = ctx.get("status", "")
        updated_at = format_datetime(ctx.get("updatedAt", ""))

        # 截断过长的字段
        if len(title) > 18:
            title = title[:18] + ".."
        if len(assignee) > 13:
            assignee = assignee[:13] + ".."

        print(f"{context_id:<35} {title:<20} {assignee:<15} {status:<12} {updated_at:<16}")

    print()
    print(f"共 {len(contexts)} 个上下文")


def main():
    parser = argparse.ArgumentParser(description="列出开发上下文")
    parser.add_argument("--all", action="store_true", help="列出所有上下文（包括已归档）")

    args = parser.parse_args()

    try:
        # 查找项目根目录
        project_root = find_project_root()

        # 读取索引文件
        index_path = project_root / "docs" / "contexts" / ".contexts-index.json"
        if not index_path.exists():
            print("错误: 索引文件不存在", file=sys.stderr)
            print("提示: 使用 init_context.py 创建第一个上下文", file=sys.stderr)
            sys.exit(1)

        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)

        # 打印活跃上下文
        active_contexts = index.get("activeContexts", [])
        print_contexts(active_contexts, "📋 活跃上下文列表")

        # 如果指定了 --all，打印已归档上下文
        if args.all:
            archived_contexts = index.get("archivedContexts", [])
            print_contexts(archived_contexts, "📦 已归档上下文列表")

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
