#!/usr/bin/env python3
"""
归档已完成的开发上下文

用法:
    python scripts/archive_context.py <context-id>

示例:
    python scripts/archive_context.py 2026-02-01_user-authentication
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


def read_context_metadata(context_dir: Path) -> dict:
    """读取上下文元数据"""
    metadata_path = context_dir / ".context.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"元数据文件不存在: {metadata_path}")

    with open(metadata_path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_context_metadata(context_dir: Path, metadata: dict):
    """更新上下文元数据"""
    metadata_path = context_dir / ".context.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def generate_summary(context_dir: Path, metadata: dict) -> str:
    """生成归档摘要"""
    context_id = metadata["contextId"]
    title = metadata["title"]
    assignee = metadata["assignee"]
    created_at = metadata["createdAt"]
    completed_at = metadata["completedAt"]
    git_branch = metadata.get("gitBranch", "")
    static_docs = metadata.get("staticDocsUpdated", [])

    # 读取各个文档的内容（如果存在）
    requirements = ""
    if (context_dir / "requirements.md").exists():
        requirements = (context_dir / "requirements.md").read_text(encoding="utf-8")

    architecture_changes = ""
    if (context_dir / "architecture-changes.md").exists():
        architecture_changes = (context_dir / "architecture-changes.md").read_text(encoding="utf-8")

    test_plan = ""
    if (context_dir / "test-plan.md").exists():
        test_plan = (context_dir / "test-plan.md").read_text(encoding="utf-8")

    summary = f"""# 归档摘要 - {title}

## 基本信息

- **Context ID**: {context_id}
- **功能标题**: {title}
- **负责人**: {assignee}
- **开始日期**: {created_at.split('T')[0]}
- **完成日期**: {completed_at.split('T')[0]}
- **Git 分支**: {git_branch}

## 完成状态

### 已实现功能

请根据实际情况填写：

- [x] 功能 1
- [x] 功能 2

### 未实现功能

- [ ] 功能 X（原因：）

### 技术栈

请根据实际情况填写：

- 前端：
- 后端：
- 数据库：
- 其他：

## 关键决策

### 决策 1：[决策标题]

- **背景**：
- **决策**：
- **影响**：

## 问题和解决方案

### 问题 1：[问题描述]

- **影响**：
- **解决方案**：
- **经验教训**：

## 测试结果

请根据实际情况填写：

- **单元测试覆盖率**：
- **集成测试**：
- **E2E 测试**：
- **性能测试**：
- **安全测试**：

## 更新的静态文档

"""

    if static_docs:
        for doc in static_docs:
            summary += f"- `{doc}`\n"
    else:
        summary += "无\n"

    summary += """
## 后续工作

### 技术债务

- 技术债务 1：
- 技术债务 2：

### 改进建议

- 改进 1：
- 改进 2：

### 未来功能

- 功能 1：
- 功能 2：

## 经验总结

### 做得好的地方

- 经验 1
- 经验 2

### 需要改进的地方

- 改进点 1
- 改进点 2

### 关键经验

- 经验 1：详细描述
- 经验 2：详细描述

## 参考资料

- 相关文档链接
- 外部资源
- 会议记录

---

**注意**: 此摘要由脚本自动生成，请根据实际情况补充和修改。
"""

    return summary


def update_index(index_path: Path, context_id: str):
    """更新索引：将上下文从活跃移至已归档"""
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    # 从活跃上下文中移除
    active_contexts = index.get("activeContexts", [])
    context_to_archive = None
    for i, ctx in enumerate(active_contexts):
        if ctx["contextId"] == context_id:
            context_to_archive = active_contexts.pop(i)
            break

    if not context_to_archive:
        raise ValueError(f"在活跃上下文中未找到: {context_id}")

    # 添加到已归档上下文
    archived_contexts = index.get("archivedContexts", [])
    archived_contexts.append(context_to_archive)

    # 保存索引
    index["activeContexts"] = active_contexts
    index["archivedContexts"] = archived_contexts

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="归档已完成的开发上下文")
    parser.add_argument("context_id", help="要归档的上下文 ID（如：2026-02-01_user-authentication）")

    args = parser.parse_args()

    try:
        # 查找项目根目录
        project_root = find_project_root()
        print(f"项目根目录: {project_root}")

        # 检查上下文目录是否存在
        context_dir = project_root / "docs" / "contexts" / args.context_id
        if not context_dir.exists():
            print(f"错误: 上下文目录不存在: {context_dir}", file=sys.stderr)
            sys.exit(1)

        print(f"上下文目录: {context_dir}")

        # 读取元数据
        metadata = read_context_metadata(context_dir)
        print(f"当前状态: {metadata['status']}")

        # 更新元数据
        now = datetime.now().isoformat() + "Z"
        metadata["status"] = "completed"
        metadata["completedAt"] = now
        metadata["updatedAt"] = now

        update_context_metadata(context_dir, metadata)
        print("✅ 更新元数据: status = completed")

        # 生成归档摘要
        summary = generate_summary(context_dir, metadata)
        summary_path = context_dir / "SUMMARY.md"
        summary_path.write_text(summary, encoding="utf-8")
        print(f"✅ 生成归档摘要: {summary_path}")

        # 更新索引
        index_path = project_root / "docs" / "contexts" / ".contexts-index.json"
        update_index(index_path, args.context_id)
        print(f"✅ 更新索引: 移至已归档上下文")

        print(f"\n✅ 成功归档上下文: {args.context_id}")
        print(f"\n下一步:")
        print(f"1. 审查并完善 {summary_path}")
        print(f"2. 提取关键经验到项目文档")
        print(f"3. 处理后续工作和技术债务")

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
