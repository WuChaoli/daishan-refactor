#!/usr/bin/env python3
"""
Initialize a new development context with directory structure, metadata, and initial documents.

Usage:
    python init_context.py <feature-name> [--assignee <name>] [--branch <branch-name>]

Example:
    python init_context.py user-authentication --assignee developer --branch feature/user-auth
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def generate_context_id(feature_name: str) -> str:
    """Generate contextId in format YYYY-MM-DD_feature-name"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    # Convert to lowercase and replace spaces with hyphens
    feature_slug = feature_name.lower().replace(" ", "-").replace("_", "-")
    return f"{date_str}_{feature_slug}"


def create_context_metadata(
    context_id: str,
    title: str,
    description: str,
    assignee: str,
    git_branch: str
) -> dict:
    """Create .context.json metadata"""
    now = datetime.now().isoformat() + "Z"
    return {
        "contextId": context_id,
        "status": "in_progress",
        "createdAt": now,
        "updatedAt": now,
        "completedAt": None,
        "title": title,
        "description": description,
        "assignee": assignee,
        "gitBranch": git_branch,
        "documents": {
            "requirements": "requirements.md",
            "architectureChanges": "architecture-changes.md",
            "featureSpec": "feature-spec.md",
            "plan": "plan.md",
            "todos": "todos.md",
            "testPlan": "test-plan.md"
        },
        "staticDocsUpdated": []
    }


def load_template(template_path: Path, feature_name: str) -> str:
    """Load and customize a template"""
    if not template_path.exists():
        return f"# {feature_name}\n\n[Template not found: {template_path}]\n"

    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace placeholder
    return content.replace("[功能名称]", feature_name)


def init_context(
    feature_name: str,
    assignee: str = "developer",
    git_branch: str = None,
    description: str = None
):
    """Initialize a new development context"""

    # Generate context ID
    context_id = generate_context_id(feature_name)

    # Set defaults
    if git_branch is None:
        git_branch = f"feature/{feature_name.lower().replace(' ', '-')}"
    if description is None:
        description = f"实现{feature_name}功能"

    # Find project root (look for docs/contexts/)
    current_dir = Path.cwd()
    project_root = current_dir
    while project_root != project_root.parent:
        if (project_root / "docs" / "contexts").exists():
            break
        project_root = project_root.parent
    else:
        print("❌ Error: Could not find docs/contexts/ directory")
        print("   Please run this script from within the project directory")
        return False

    # Create context directory
    context_dir = project_root / "docs" / "contexts" / context_id
    if context_dir.exists():
        print(f"❌ Error: Context {context_id} already exists")
        return False

    context_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created context directory: {context_dir}")

    # Create metadata
    metadata = create_context_metadata(
        context_id, feature_name, description, assignee, git_branch
    )
    metadata_path = context_dir / ".context.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"✅ Created metadata: .context.json")

    # Load templates from docs/static/development/
    templates_dir = project_root / "docs" / "static" / "development"

    # Create initial documents (simplified templates)
    documents = {
        "requirements.md": f"""# 需求文档 - {feature_name}

## 背景
[描述需求的背景和动机]

## 目标
[明确的目标列表]

## 功能需求
### 核心功能
- [功能点 1]
- [功能点 2]

### 非功能需求
- 性能要求
- 安全要求
- 可用性要求

## 约束条件
[技术约束、时间约束等]

## 验收标准
- [ ] 标准 1
- [ ] 标准 2
""",
        "architecture-changes.md": f"""# 架构变更 - {feature_name}

## 变更概述
[简要描述架构变更]

## 影响的组件
- 组件 A: [变更说明]
- 组件 B: [变更说明]

## 新增组件
### 组件名称
- **职责**: [组件职责]
- **接口**: [对外接口]
- **依赖**: [依赖的其他组件]

## 数据模型变更
[数据库 schema 变更、新增表等]

## API 变更
### 新增 API
- `POST /api/endpoint` - [说明]

### 修改 API
- `GET /api/endpoint` - [变更说明]

## 架构决策
### ADR-001: [决策标题]
- **状态**: 已接受
- **上下文**: [决策背景]
- **决策**: [具体决策]
- **后果**: [决策带来的影响]

## 需要更新的静态文档
- [ ] docs/static/architecture/system-context.md
- [ ] docs/static/api/[endpoint].md
""",
        "feature-spec.md": f"""# 功能规格 - {feature_name}

## 功能概述
[功能的详细描述]

## 用户界面
### 页面/组件 1
- **路径**: /path
- **布局**: [描述]
- **交互**: [描述]

## 业务逻辑
### 流程 1
1. 步骤 1
2. 步骤 2
3. 步骤 3

## 数据流
```
用户 -> 前端 -> API -> 服务层 -> 数据库
```

## 错误处理
- 错误场景 1: [处理方式]
- 错误场景 2: [处理方式]

## 边界情况
- 场景 1: [处理方式]
- 场景 2: [处理方式]
""",
        "plan.md": f"""# 实施计划 - {feature_name}

## 阶段划分
### Phase 1: [阶段名称]
**目标**: [阶段目标]

**任务**:
- [ ] 任务 1
- [ ] 任务 2

**预期产出**:
- 产出 1
- 产出 2

### Phase 2: [阶段名称]
[同上]

## 依赖关系
- Phase 2 依赖 Phase 1 完成
- 外部依赖: [说明]

## 风险评估
### 风险 1
- **描述**: [风险描述]
- **影响**: 高/中/低
- **缓解措施**: [措施]
""",
        "test-plan.md": f"""# 测试计划 - {feature_name}

## 测试策略
- 单元测试覆盖率目标: 80%+
- 集成测试: [说明]
- E2E 测试: [说明]

## 测试用例
### 功能测试
#### TC-001: [测试用例名称]
- **前置条件**: [条件]
- **测试步骤**:
  1. 步骤 1
  2. 步骤 2
- **预期结果**: [结果]
- **状态**: ⬜ 未测试 / ✅ 通过 / ❌ 失败

### 性能测试
- 场景 1: [描述]
- 预期指标: [指标]

### 安全测试
- [ ] SQL 注入测试
- [ ] XSS 测试
- [ ] 认证授权测试

## 测试环境
- 开发环境: [说明]
- 测试环境: [说明]

## 测试数据
[测试数据准备说明]
"""
    }

    # Write documents
    for filename, content in documents.items():
        doc_path = context_dir / filename
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Created document: {filename}")

    # Update index file
    index_path = project_root / "docs" / "contexts" / ".contexts-index.json"
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
    else:
        index_data = {"activeContexts": [], "archivedContexts": []}

    # Add to active contexts
    index_data["activeContexts"].append({
        "contextId": context_id,
        "title": feature_name,
        "status": "in_progress",
        "assignee": assignee,
        "updatedAt": metadata["updatedAt"]
    })

    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Updated index: .contexts-index.json")

    # Print summary
    print(f"\n✅ 已创建上下文：{context_id}")
    print(f"\n📁 目录：docs/contexts/{context_id}/")
    print(f"📄 已创建文档：")
    for filename in documents.keys():
        print(f"  - {filename}")
    print(f"\n下一步：")
    print(f"1. 编辑 requirements.md 填写需求详情")
    print(f"2. 更新 plan.md 制定实施计划")
    print(f"3. 开始开发")

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python init_context.py <feature-name> [--assignee <name>] [--branch <branch-name>]")
        sys.exit(1)

    feature_name = sys.argv[1]
    assignee = "developer"
    git_branch = None

    # Parse optional arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--assignee" and i + 1 < len(sys.argv):
            assignee = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--branch" and i + 1 < len(sys.argv):
            git_branch = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    success = init_context(feature_name, assignee, git_branch)
    sys.exit(0 if success else 1)
