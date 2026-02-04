#!/usr/bin/env python3
"""
初始化新的开发上下文

用法:
    python scripts/init_context.py <feature-name> [--assignee <name>] [--branch <branch-name>]

示例:
    python scripts/init_context.py user-authentication --assignee developer --branch feature/user-auth
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def find_project_root():
    """查找项目根目录（包含 docs/contexts/ 的目录）"""
    current = Path.cwd()
    while current != current.parent:
        if (current / "docs" / "contexts").exists():
            return current
        current = current.parent
    raise FileNotFoundError("无法找到项目根目录（未找到 docs/contexts/ 目录）")


def generate_context_id(feature_name: str) -> str:
    """生成上下文 ID: YYYY-MM-DD_feature-name"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    return f"{date_str}_{feature_name}"


def create_context_metadata(context_id: str, title: str, description: str, assignee: str, git_branch: str) -> dict:
    """创建上下文元数据"""
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


def create_initial_documents(context_dir: Path, title: str):
    """创建初始文档"""

    # requirements.md
    (context_dir / "requirements.md").write_text(f"""# 需求文档 - {title}

## 概述

简要描述此功能的目的和价值。

## 背景

- 为什么需要这个功能？
- 解决什么问题？
- 业务价值是什么？

## 功能需求

### 核心功能

1. **功能点 1**
   - 描述
   - 用户故事：作为 [角色]，我想要 [功能]，以便 [价值]
   - 验收标准

### 非功能需求

- **性能要求**：
- **安全要求**：
- **可用性要求**：
- **可维护性要求**：

## 用户场景

### 场景 1：[场景名称]

1. 用户操作步骤
2. 系统响应
3. 预期结果

## 约束条件

- 技术约束
- 时间约束
- 资源约束

## 成功标准

- 如何衡量功能是否成功？
- 关键指标是什么？
""", encoding="utf-8")

    # architecture-changes.md
    (context_dir / "architecture-changes.md").write_text(f"""# 架构变更 - {title}

## 概述

简要描述此功能对系统架构的影响。

## 影响的组件

### 新增组件

- **组件名称**
  - 职责
  - 接口
  - 依赖

### 修改的组件

- **组件名称**
  - 当前状态
  - 变更内容
  - 变更原因

## 架构决策

### 决策 1：[决策标题]

- **状态**：待定
- **背景**：
- **决策**：
- **后果**：
- **备选方案**：

## 数据模型变更

### 新增表/集合

```sql
-- 数据库 schema
```

## API 变更

### 新增 API

- **端点**：
- **描述**：
- **请求格式**：
- **响应格式**：

## 依赖关系

### 新增依赖

- **依赖名称**：版本
  - 用途
  - 许可证

## 性能影响

- 预期的性能影响
- 优化策略

## 安全考虑

- 安全风险
- 缓解措施

## 更新的静态文档

- [ ] `docs/static/architecture/`
- [ ] `docs/static/api/`
""", encoding="utf-8")

    # feature-spec.md
    (context_dir / "feature-spec.md").write_text(f"""# 功能规格 - {title}

## 概述

详细的功能规格说明。

## 用户界面

### 界面 1：[界面名称]

- **布局**：
- **元素**：
- **交互**：
- **状态**：

## 业务逻辑

### 流程 1：[流程名称]

```
1. 用户触发操作
2. 系统验证输入
3. 系统处理请求
4. 系统返回结果
```

## 数据流

```
用户输入 -> 前端验证 -> API 请求 -> 后端处理 -> 数据库操作 -> 响应返回
```

## 错误处理

### 错误场景 1

- **触发条件**：
- **错误消息**：
- **用户操作**：
- **系统行为**：

## 边界条件

- 最大/最小值
- 空值处理
- 并发处理
- 超时处理
""", encoding="utf-8")

    # plan.md
    (context_dir / "plan.md").write_text(f"""# 实施计划 - {title}

## 概述

实施此功能的详细计划。

## 阶段划分

### 阶段 1：[阶段名称]

- **目标**：
- **任务**：
  1. 任务 1
  2. 任务 2
- **交付物**：
- **依赖**：
- **风险**：

## 任务清单

- [ ] 任务 1：描述
  - 负责人：
  - 状态：待开始
- [ ] 任务 2：描述
  - 负责人：
  - 状态：待开始

## 里程碑

1. **里程碑 1**：日期
   - 完成标准
   - 验收标准

## 依赖关系

- **外部依赖**：
- **内部依赖**：

## 风险管理

| 风险 | 影响 | 概率 | 缓解措施 | 负责人 |
|------|------|------|----------|--------|
| 风险 1 | 高/中/低 | 高/中/低 | 措施 | 姓名 |

## 资源需求

- **人力资源**：
- **技术资源**：

## 回滚计划

1. 回滚步骤 1
2. 回滚步骤 2
""", encoding="utf-8")

    # test-plan.md
    (context_dir / "test-plan.md").write_text(f"""# 测试计划 - {title}

## 概述

此功能的测试策略和计划。

## 测试范围

### 包含的功能

- 功能 1
- 功能 2

### 不包含的功能

- 功能 X（原因）

## 测试策略

### 单元测试

- **覆盖率目标**：80%+
- **测试框架**：pytest
- **重点测试**：
  - 业务逻辑
  - 边界条件
  - 错误处理

### 集成测试

- **测试范围**：
  - API 集成
  - 数据库集成
  - 第三方服务集成

### 端到端测试

- **测试场景**：
  - 场景 1：描述
  - 场景 2：描述

## 测试用例

| ID | 测试场景 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |
|----|----------|----------|----------|----------|--------|
| TC-001 | 场景描述 | 条件 | 步骤 | 结果 | 高 |

## 测试环境

- **开发环境**：
- **测试环境**：

## 验收标准

- [ ] 所有 P0/P1 缺陷已修复
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 所有集成测试通过
- [ ] 所有 E2E 测试通过
""", encoding="utf-8")

    # todos.md
    (context_dir / "todos.md").write_text(f"""# 任务清单 - {title}

## 待办任务

### 高优先级

- [ ] 任务 1
  - 描述
  - 负责人：
  - 截止日期：

### 中优先级

- [ ] 任务 2

### 低优先级

- [ ] 任务 3

## 进行中

- [ ] 任务 X
  - 开始日期：
  - 负责人：
  - 进度：

## 已完成

- [x] 任务 Y
  - 完成日期：
  - 负责人：

## 阻塞任务

- [ ] 任务 Z
  - 阻塞原因：
  - 解决方案：
""", encoding="utf-8")


def update_index(index_path: Path, context_metadata: dict):
    """更新上下文索引"""
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
    else:
        index = {"activeContexts": [], "archivedContexts": []}

    # 添加到活跃上下文
    index["activeContexts"].append({
        "contextId": context_metadata["contextId"],
        "title": context_metadata["title"],
        "status": context_metadata["status"],
        "assignee": context_metadata["assignee"],
        "updatedAt": context_metadata["updatedAt"]
    })

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="初始化新的开发上下文")
    parser.add_argument("feature_name", help="功能名称（使用小写英文和连字符，如：user-authentication）")
    parser.add_argument("--assignee", default="developer", help="负责人姓名")
    parser.add_argument("--branch", help="Git 分支名称")
    parser.add_argument("--title", help="功能标题（中文）")
    parser.add_argument("--description", help="功能描述")

    args = parser.parse_args()

    try:
        # 查找项目根目录
        project_root = find_project_root()
        print(f"项目根目录: {project_root}")

        # 生成上下文 ID
        context_id = generate_context_id(args.feature_name)
        print(f"上下文 ID: {context_id}")

        # 创建上下文目录
        context_dir = project_root / "docs" / "contexts" / context_id
        if context_dir.exists():
            print(f"错误: 上下文目录已存在: {context_dir}", file=sys.stderr)
            sys.exit(1)

        context_dir.mkdir(parents=True)
        print(f"创建上下文目录: {context_dir}")

        # 准备元数据
        title = args.title or args.feature_name.replace("-", " ").title()
        description = args.description or f"实现 {title} 功能"
        git_branch = args.branch or f"feature/{args.feature_name}"

        metadata = create_context_metadata(
            context_id=context_id,
            title=title,
            description=description,
            assignee=args.assignee,
            git_branch=git_branch
        )

        # 保存元数据
        metadata_path = context_dir / ".context.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"创建元数据文件: {metadata_path}")

        # 创建初始文档
        create_initial_documents(context_dir, title)
        print("创建初始文档")

        # 更新索引
        index_path = project_root / "docs" / "contexts" / ".contexts-index.json"
        update_index(index_path, metadata)
        print(f"更新索引文件: {index_path}")

        print(f"\n✅ 成功初始化上下文: {context_id}")
        print(f"\n下一步:")
        print(f"1. 编辑 {context_dir}/requirements.md 填写需求详情")
        print(f"2. 更新 {context_dir}/plan.md 创建实施计划")
        print(f"3. 开始开发")

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
