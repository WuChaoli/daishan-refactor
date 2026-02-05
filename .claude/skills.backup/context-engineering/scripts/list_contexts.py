#!/usr/bin/env python3
"""
List all active development contexts.

Usage:
    python list_contexts.py [--all]

Options:
    --all    Show both active and archived contexts
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def format_timestamp(iso_timestamp: str) -> str:
    """Format ISO timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return iso_timestamp


def list_contexts(show_all: bool = False):
    """List active (and optionally archived) contexts"""

    # Find project root
    current_dir = Path.cwd()
    project_root = current_dir
    while project_root != project_root.parent:
        if (project_root / "docs" / "contexts").exists():
            break
        project_root = project_root.parent
    else:
        print("❌ Error: Could not find docs/contexts/ directory")
        return False

    # Read index file
    index_path = project_root / "docs" / "contexts" / ".contexts-index.json"
    if not index_path.exists():
        print("📋 No contexts found")
        print("\nTo create a new context, run:")
        print("  python init_context.py <feature-name>")
        return True

    with open(index_path, 'r', encoding='utf-8') as f:
        index_data = json.load(f)

    active_contexts = index_data.get("activeContexts", [])
    archived_contexts = index_data.get("archivedContexts", [])

    # Display active contexts
    if active_contexts:
        print("📋 活跃上下文列表：\n")
        print(f"{'Context ID':<35} {'标题':<20} {'负责人':<15} {'状态':<12} {'最后更新':<20}")
        print("-" * 110)
        for ctx in active_contexts:
            context_id = ctx.get("contextId", "")
            title = ctx.get("title", "")
            assignee = ctx.get("assignee", "")
            status = ctx.get("status", "")
            updated_at = format_timestamp(ctx.get("updatedAt", ""))
            print(f"{context_id:<35} {title:<20} {assignee:<15} {status:<12} {updated_at:<20}")
        print(f"\n共 {len(active_contexts)} 个活跃上下文")
    else:
        print("📋 没有活跃的上下文")

    # Display archived contexts if requested
    if show_all and archived_contexts:
        print("\n\n📦 归档上下文列表：\n")
        print(f"{'Context ID':<35} {'标题':<20} {'负责人':<15} {'状态':<12} {'完成时间':<20}")
        print("-" * 110)
        for ctx in archived_contexts:
            context_id = ctx.get("contextId", "")
            title = ctx.get("title", "")
            assignee = ctx.get("assignee", "")
            status = ctx.get("status", "")
            completed_at = format_timestamp(ctx.get("completedAt", ""))
            print(f"{context_id:<35} {title:<20} {assignee:<15} {status:<12} {completed_at:<20}")
        print(f"\n共 {len(archived_contexts)} 个归档上下文")

    return True


if __name__ == "__main__":
    show_all = "--all" in sys.argv
    success = list_contexts(show_all)
    sys.exit(0 if success else 1)
