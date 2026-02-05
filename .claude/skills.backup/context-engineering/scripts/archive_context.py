#!/usr/bin/env python3
"""
Archive a completed development context.

Usage:
    python archive_context.py <context-id>

Example:
    python archive_context.py 2026-02-01_user-authentication
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def generate_summary(context_dir: Path, metadata: dict) -> str:
    """Generate SUMMARY.md content"""
    context_id = metadata.get("contextId", "")
    title = metadata.get("title", "")
    assignee = metadata.get("assignee", "")
    git_branch = metadata.get("gitBranch", "")
    created_at = metadata.get("createdAt", "")
    completed_at = metadata.get("completedAt", "")

    summary = f"""# 归档总结 - {title}

## 基本信息
- **Context ID**: {context_id}
- **开始时间**: {created_at.split('T')[0] if 'T' in created_at else created_at}
- **完成时间**: {completed_at.split('T')[0] if 'T' in completed_at else completed_at}
- **负责人**: {assignee}
- **Git 分支**: {git_branch}

## 完成情况
### 实现的功能
"""

    # Try to read requirements.md for implemented features
    req_path = context_dir / "requirements.md"
    if req_path.exists():
        summary += "[从 requirements.md 中提取]\n\n"
    else:
        summary += "- [功能 1]\n- [功能 2]\n\n"

    summary += """### 技术栈
- [技术 1]
- [技术 2]

## 关键决策
"""

    # Try to read architecture-changes.md for key decisions
    arch_path = context_dir / "architecture-changes.md"
    if arch_path.exists():
        summary += "[从 architecture-changes.md 中提取]\n\n"
    else:
        summary += "1. **决策 1**: [说明]\n2. **决策 2**: [说明]\n\n"

    summary += """## 遇到的问题及解决方案
### 问题 1
- **描述**: [问题描述]
- **解决方案**: [方案]
- **经验教训**: [教训]

## 测试结果
"""

    # Try to read test-plan.md for test results
    test_path = context_dir / "test-plan.md"
    if test_path.exists():
        summary += "[从 test-plan.md 中提取]\n\n"
    else:
        summary += "- 单元测试覆盖率: XX%\n- 集成测试: 通过/失败\n- E2E 测试: 通过/失败\n\n"

    # Add updated static docs
    static_docs = metadata.get("staticDocsUpdated", [])
    if static_docs:
        summary += "## 更新的静态文档\n"
        for doc in static_docs:
            summary += f"- {doc}\n"
        summary += "\n"
    else:
        summary += """## 更新的静态文档
- docs/static/architecture/[file]
- docs/static/api/[file]

"""

    summary += """## 后续工作
- [ ] 待办事项 1
- [ ] 待办事项 2

## 经验总结
[关键经验和最佳实践]
"""

    return summary


def archive_context(context_id: str):
    """Archive a development context"""

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

    # Verify context exists
    context_dir = project_root / "docs" / "contexts" / context_id
    if not context_dir.exists():
        print(f"❌ Error: Context {context_id} does not exist")
        return False

    # Read metadata
    metadata_path = context_dir / ".context.json"
    if not metadata_path.exists():
        print(f"❌ Error: Metadata file not found for context {context_id}")
        return False

    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    # Check if already archived
    if metadata.get("status") == "completed":
        print(f"⚠️  Warning: Context {context_id} is already archived")
        return True

    # Update metadata
    now = datetime.now().isoformat() + "Z"
    metadata["status"] = "completed"
    metadata["completedAt"] = now
    metadata["updatedAt"] = now

    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"✅ Updated metadata: status → completed")

    # Generate SUMMARY.md
    summary_content = generate_summary(context_dir, metadata)
    summary_path = context_dir / "SUMMARY.md"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary_content)
    print(f"✅ Generated summary: SUMMARY.md")

    # Update index file
    index_path = project_root / "docs" / "contexts" / ".contexts-index.json"
    if not index_path.exists():
        print("❌ Error: Index file not found")
        return False

    with open(index_path, 'r', encoding='utf-8') as f:
        index_data = json.load(f)

    # Move from active to archived
    active_contexts = index_data.get("activeContexts", [])
    archived_contexts = index_data.get("archivedContexts", [])

    # Find and remove from active
    context_entry = None
    for i, ctx in enumerate(active_contexts):
        if ctx.get("contextId") == context_id:
            context_entry = active_contexts.pop(i)
            break

    if context_entry:
        # Update entry
        context_entry["status"] = "completed"
        context_entry["completedAt"] = now
        context_entry["updatedAt"] = now

        # Add to archived
        archived_contexts.append(context_entry)

        # Save index
        index_data["activeContexts"] = active_contexts
        index_data["archivedContexts"] = archived_contexts

        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Updated index: moved to archived")
    else:
        print(f"⚠️  Warning: Context not found in active list")

    # Print summary
    print(f"\n✅ 已归档上下文：{context_id}")
    print(f"\n📊 归档总结：docs/contexts/{context_id}/SUMMARY.md")
    print(f"📈 状态：in_progress → completed")
    print(f"📅 完成时间：{now}")
    print(f"\n归档信息已更新到索引文件。")

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python archive_context.py <context-id>")
        print("\nExample:")
        print("  python archive_context.py 2026-02-01_user-authentication")
        sys.exit(1)

    context_id = sys.argv[1]
    success = archive_context(context_id)
    sys.exit(0 if success else 1)
