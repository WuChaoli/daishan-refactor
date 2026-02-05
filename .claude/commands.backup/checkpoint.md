---
description: Create and manage checkpoints during development workflow
---

# Workflow Checkpoint Command

在开发工作流的各个阶段创建检查点，支持回滚、对比和验证。

## Usage

```bash
/workflow-checkpoint [action] [name] [options]
```

## Actions

### create
创建工作流检查点

```bash
/workflow-checkpoint create <checkpoint-name>
```

### verify
验证当前状态与检查点的差异

```bash
/workflow-checkpoint verify <checkpoint-name>
```

### rollback
回滚到指定检查点

```bash
/workflow-checkpoint rollback <checkpoint-name>
```

### list
列出所有检查点

```bash
/workflow-checkpoint list [context-id]
```

### compare
对比两个检查点

```bash
/workflow-checkpoint compare <checkpoint-1> <checkpoint-2>
```

### clean
清理旧检查点

```bash
/workflow-checkpoint clean [--keep=5]
```

## Checkpoint Structure

每个检查点包含以下信息：

```json
{
  "id": "2026-02-01_user-auth_requirement-done",
  "contextId": "2026-02-01_user-auth",
  "name": "requirement-done",
  "timestamp": "2026-02-01T10:30:00Z",
  "stage": "code-new-requirement",
  "gitCommit": "abc123",
  "files": {
    "added": ["docs/contexts/2026-02-01_user-auth/requirements.md"],
    "modified": [],
    "deleted": []
  },
  "tests": {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "coverage": 0
  },
  "metadata": {
    "description": "需求分析完成",
    "agent": "code-new-requirement",
    "status": "success"
  }
}
```

## Create Checkpoint

### 执行流程

1. **收集当前状态**
   ```bash
   # Git 状态
   git status --porcelain
   git rev-parse HEAD

   # 文件变更
   git diff --name-status

   # 测试状态（如果有）
   npm test -- --coverage --json
   ```

2. **创建 Git 提交或 Stash**
   ```bash
   # 选项 1: 创建提交
   git add .
   git commit -m "checkpoint: $CHECKPOINT_NAME"

   # 选项 2: 创建 stash
   git stash push -m "checkpoint: $CHECKPOINT_NAME"
   ```

3. **保存检查点元数据**
   ```bash
   # 保存到上下文目录
   echo "$CHECKPOINT_JSON" > docs/contexts/$CONTEXT_ID/.checkpoints/$CHECKPOINT_ID.json

   # 更新检查点索引
   echo "$CHECKPOINT_ENTRY" >> docs/contexts/$CONTEXT_ID/.checkpoints/index.log
   ```

4. **报告检查点创建**
   ```markdown
   ✓ 检查点已创建: requirement-done

   Context: 2026-02-01_user-auth
   Stage: code-new-requirement
   Git: abc123
   Files: 1 added, 0 modified, 0 deleted
   Tests: N/A

   检查点 ID: 2026-02-01_user-auth_requirement-done
   ```

### 预定义检查点名称

为 dev-workflow 的各个阶段预定义检查点名称：

| 阶段 | 检查点名称 | 描述 |
|------|-----------|------|
| 开始 | `workflow-start` | 工作流开始前的初始状态 |
| 需求分析后 | `requirement-done` | 需求分析完成 |
| 架构设计后 | `architecture-done` | 架构设计完成 |
| 开发计划后 | `plan-done` | 开发计划完成 |
| TDD 开发后 | `implementation-done` | 代码实现完成 |
| 文档更新后 | `documentation-done` | 文档更新完成 |
| 工作流结束 | `workflow-complete` | 工作流全部完成 |

### 自动检查点

在 dev-workflow 中自动创建检查点：

```markdown
## Dev Workflow 集成

在每个 agent 执行后自动创建检查点：

1. Agent 执行前: 创建 `before-{agent-name}` 检查点
2. Agent 执行后: 创建 `after-{agent-name}` 检查点

示例:
- before-code-new-requirement
- after-code-new-requirement
- before-code-architect
- after-code-architect
```

## Verify Checkpoint

### 执行流程

1. **读取检查点元数据**
   ```bash
   cat docs/contexts/$CONTEXT_ID/.checkpoints/$CHECKPOINT_ID.json
   ```

2. **对比当前状态**
   ```bash
   # 文件变更
   git diff --name-status $CHECKPOINT_COMMIT HEAD

   # 测试变化
   npm test -- --coverage --json
   ```

3. **生成对比报告**
   ```markdown
   ## 检查点验证: requirement-done

   ### 基本信息
   - 检查点时间: 2026-02-01 10:30:00
   - 当前时间: 2026-02-01 15:45:00
   - 时间差: 5小时15分钟

   ### Git 状态
   - 检查点提交: abc123
   - 当前提交: def456
   - 提交差异: +5 commits

   ### 文件变更
   自检查点以来的变更:
   - 新增: 8 个文件
   - 修改: 3 个文件
   - 删除: 0 个文件

   详细列表:
   + src/models/User.ts
   + src/services/AuthService.ts
   + test/unit/AuthService.test.ts
   M docs/contexts/2026-02-01_user-auth/plan.md
   M package.json

   ### 测试状态
   检查点时:
   - 总数: 0
   - 通过: 0
   - 失败: 0
   - 覆盖率: 0%

   当前:
   - 总数: 45
   - 通过: 45
   - 失败: 0
   - 覆盖率: 85%

   变化: +45 tests, +85% coverage

   ### 构建状态
   - 检查点时: N/A
   - 当前: ✓ PASS

   ### 评估
   ✓ 进展良好
   - 文件变更合理
   - 测试覆盖率达标
   - 构建通过
   ```

## Rollback Checkpoint

### 执行流程

1. **确认回滚操作**
   ```markdown
   ⚠️ 警告: 回滚操作将丢失当前未提交的更改

   回滚到: requirement-done (2026-02-01 10:30:00)
   将丢失:
   - 8 个新增文件
   - 3 个修改文件
   - 45 个测试

   是否继续? [y/N]
   ```

2. **创建安全备份**
   ```bash
   # 备份当前状态
   git stash push -m "backup-before-rollback-$(date +%s)"
   ```

3. **执行回滚**
   ```bash
   # 方式 1: 回滚到提交
   git reset --hard $CHECKPOINT_COMMIT

   # 方式 2: 应用 stash
   git stash apply stash@{$STASH_INDEX}
   ```

4. **验证回滚**
   ```bash
   # 验证文件状态
   git status

   # 验证测试
   npm test
   ```

5. **报告回滚结果**
   ```markdown
   ✓ 已回滚到检查点: requirement-done

   回滚详情:
   - 目标提交: abc123
   - 删除文件: 8 个
   - 恢复文件: 0 个
   - 备份位置: stash@{0}

   如需恢复回滚前的状态:
   git stash pop stash@{0}
   ```

## List Checkpoints

### 执行流程

1. **读取检查点索引**
   ```bash
   # 读取特定上下文的检查点
   cat docs/contexts/$CONTEXT_ID/.checkpoints/index.log

   # 或读取所有上下文的检查点
   find docs/contexts -name "index.log" -path "*/.checkpoints/*"
   ```

2. **格式化输出**
   ```markdown
   ## 检查点列表

   Context: 2026-02-01_user-auth

   | ID | 名称 | 阶段 | 时间 | Git | 状态 |
   |----|------|------|------|-----|------|
   | 1 | workflow-start | - | 02-01 09:00 | abc123 | ✓ |
   | 2 | requirement-done | code-new-requirement | 02-01 10:30 | def456 | ✓ |
   | 3 | architecture-done | code-architect | 02-01 12:00 | ghi789 | ✓ |
   | 4 | plan-done | code-planner | 02-01 14:00 | jkl012 | ✓ |
   | 5 | implementation-done | code-tdd-dev | 02-01 16:30 | mno345 | → 当前 |

   总计: 5 个检查点
   当前位置: implementation-done
   ```

### 过滤选项

```bash
# 列出特定上下文的检查点
/workflow-checkpoint list 2026-02-01_user-auth

# 列出特定阶段的检查点
/workflow-checkpoint list --stage=code-architect

# 列出最近 N 个检查点
/workflow-checkpoint list --recent=10

# 列出所有上下文的检查点
/workflow-checkpoint list --all
```

## Compare Checkpoints

### 执行流程

1. **读取两个检查点**
   ```bash
   cat docs/contexts/$CONTEXT_ID/.checkpoints/$CHECKPOINT_1.json
   cat docs/contexts/$CONTEXT_ID/.checkpoints/$CHECKPOINT_2.json
   ```

2. **对比差异**
   ```bash
   # Git 差异
   git diff $COMMIT_1 $COMMIT_2 --stat
   git diff $COMMIT_1 $COMMIT_2 --name-status
   ```

3. **生成对比报告**
   ```markdown
   ## 检查点对比

   ### 基本信息
   检查点 1: requirement-done (2026-02-01 10:30)
   检查点 2: implementation-done (2026-02-01 16:30)
   时间跨度: 6小时

   ### Git 变更
   - 提交数: +8 commits
   - 提交范围: abc123...mno345

   ### 文件变更
   | 类型 | 数量 | 文件 |
   |------|------|------|
   | 新增 | 12 | src/models/*, src/services/*, test/* |
   | 修改 | 5 | package.json, plan.md, ... |
   | 删除 | 0 | - |

   详细变更:
   + src/models/User.ts (150 lines)
   + src/models/Role.ts (80 lines)
   + src/services/AuthService.ts (200 lines)
   + test/unit/AuthService.test.ts (180 lines)
   M docs/contexts/2026-02-01_user-auth/plan.md (+50, -10)
   M package.json (+5, -0)

   ### 测试变更
   | 指标 | 检查点 1 | 检查点 2 | 变化 |
   |------|---------|---------|------|
   | 总数 | 0 | 45 | +45 |
   | 通过 | 0 | 45 | +45 |
   | 失败 | 0 | 0 | 0 |
   | 覆盖率 | 0% | 85% | +85% |

   ### 代码统计
   | 语言 | 检查点 1 | 检查点 2 | 变化 |
   |------|---------|---------|------|
   | TypeScript | 0 | 1,200 | +1,200 |
   | Test | 0 | 800 | +800 |
   | Markdown | 500 | 800 | +300 |

   ### 阶段进展
   requirement-done → architecture-done → plan-done → implementation-done

   完成阶段:
   ✓ 架构设计
   ✓ 开发计划
   ✓ TDD 开发

   ### 评估
   ✓ 进展显著
   - 完成 3 个主要阶段
   - 新增 12 个文件
   - 测试覆盖率达标
   - 代码质量良好
   ```

## Clean Checkpoints

### 执行流程

1. **列出所有检查点**
   ```bash
   find docs/contexts -name "*.json" -path "*/.checkpoints/*"
   ```

2. **确定清理策略**
   ```markdown
   清理策略:
   - 保留最近 5 个检查点
   - 保留预定义检查点（workflow-start, workflow-complete）
   - 删除其他检查点

   将删除:
   - before-code-new-requirement
   - after-code-new-requirement
   - before-code-architect

   将保留:
   - workflow-start
   - requirement-done
   - architecture-done
   - plan-done
   - implementation-done

   是否继续? [y/N]
   ```

3. **执行清理**
   ```bash
   # 删除检查点文件
   rm docs/contexts/$CONTEXT_ID/.checkpoints/$CHECKPOINT_ID.json

   # 更新索引
   grep -v "$CHECKPOINT_ID" index.log > index.log.tmp
   mv index.log.tmp index.log
   ```

4. **报告清理结果**
   ```markdown
   ✓ 检查点清理完成

   删除: 3 个检查点
   保留: 5 个检查点
   释放空间: 2.5 MB
   ```

## Integration with Dev Workflow

### 自动检查点

在 dev-workflow 中集成自动检查点：

```markdown
## 工作流开始
/workflow-checkpoint create workflow-start

## Agent 执行前后
for agent in agents:
    /workflow-checkpoint create before-$agent
    execute_agent($agent)
    /workflow-checkpoint create after-$agent

## 工作流结束
/workflow-checkpoint create workflow-complete
```

### 检查点验证

在关键阶段验证检查点：

```markdown
## 开发计划完成后
/workflow-checkpoint verify plan-done

## 实施完成后
/workflow-checkpoint verify implementation-done

## 工作流结束前
/workflow-checkpoint verify workflow-start
```

### 失败恢复

如果 agent 执行失败，回滚到上一个检查点：

```markdown
## Agent 执行失败
if agent_failed:
    /workflow-checkpoint rollback before-$agent
    # 重试或跳过
```

## Storage Structure

检查点存储在上下文目录中：

```
docs/contexts/2026-02-01_user-auth/
├── .checkpoints/
│   ├── index.log                                    # 检查点索引
│   ├── 2026-02-01_user-auth_workflow-start.json   # 检查点元数据
│   ├── 2026-02-01_user-auth_requirement-done.json
│   ├── 2026-02-01_user-auth_architecture-done.json
│   ├── 2026-02-01_user-auth_plan-done.json
│   └── 2026-02-01_user-auth_implementation-done.json
├── requirements.md
├── architecture.md
├── plan.md
└── metadata.json
```

### index.log 格式

```
2026-02-01T09:00:00Z | workflow-start | - | abc123 | success
2026-02-01T10:30:00Z | requirement-done | code-new-requirement | def456 | success
2026-02-01T12:00:00Z | architecture-done | code-architect | ghi789 | success
2026-02-01T14:00:00Z | plan-done | code-planner | jkl012 | success
2026-02-01T16:30:00Z | implementation-done | code-tdd-dev | mno345 | success
```

## Examples

### Example 1: 创建检查点

```bash
# 在需求分析完成后
/workflow-checkpoint create requirement-done
```

输出:
```markdown
✓ 检查点已创建: requirement-done

Context: 2026-02-01_user-auth
Stage: code-new-requirement
Git: def456
Files: 1 added, 0 modified, 0 deleted
Tests: N/A

检查点 ID: 2026-02-01_user-auth_requirement-done
位置: docs/contexts/2026-02-01_user-auth/.checkpoints/
```

### Example 2: 验证检查点

```bash
# 验证当前状态与需求分析完成时的差异
/workflow-checkpoint verify requirement-done
```

输出:
```markdown
## 检查点验证: requirement-done

### 文件变更
自检查点以来的变更:
- 新增: 8 个文件
- 修改: 3 个文件

### 测试状态
变化: +45 tests, +85% coverage

### 评估
✓ 进展良好
```

### Example 3: 对比检查点

```bash
# 对比需求分析和实施完成两个阶段
/workflow-checkpoint compare requirement-done implementation-done
```

输出:
```markdown
## 检查点对比

时间跨度: 6小时
文件变更: +12 新增, +5 修改
测试变更: +45 tests, +85% coverage

### 评估
✓ 进展显著
```

### Example 4: 回滚检查点

```bash
# 回滚到开发计划完成时
/workflow-checkpoint rollback plan-done
```

输出:
```markdown
⚠️ 警告: 将丢失 8 个文件和 45 个测试

是否继续? [y/N] y

✓ 已回滚到检查点: plan-done
备份位置: stash@{0}
```

### Example 5: 列出检查点

```bash
# 列出当前上下文的所有检查点
/workflow-checkpoint list
```

输出:
```markdown
## 检查点列表

Context: 2026-02-01_user-auth

| ID | 名称 | 阶段 | 时间 | 状态 |
|----|------|------|------|------|
| 1 | workflow-start | - | 02-01 09:00 | ✓ |
| 2 | requirement-done | code-new-requirement | 02-01 10:30 | ✓ |
| 3 | architecture-done | code-architect | 02-01 12:00 | ✓ |
| 4 | plan-done | code-planner | 02-01 14:00 | ✓ |
| 5 | implementation-done | code-tdd-dev | 02-01 16:30 | → 当前 |

总计: 5 个检查点
```

## Tips

1. **定期创建检查点**
   - 在每个重要阶段创建检查点
   - 使用预定义的检查点名称
   - 添加描述性信息

2. **验证进展**
   - 定期验证当前状态与检查点的差异
   - 确保进展符合预期
   - 及时发现问题

3. **安全回滚**
   - 回滚前先创建备份
   - 确认回滚操作
   - 验证回滚结果

4. **对比分析**
   - 对比不同阶段的检查点
   - 分析进展和变化
   - 评估开发效率

5. **定期清理**
   - 清理旧的检查点
   - 保留重要检查点
   - 释放存储空间

## Arguments

$ARGUMENTS:
- `create <name>` - 创建检查点
- `verify <name>` - 验证检查点
- `rollback <name>` - 回滚到检查点
- `list [context-id]` - 列出检查点
- `compare <name1> <name2>` - 对比检查点
- `clean [--keep=N]` - 清理检查点

## Related Commands

- `/dev-workflow` - 开发工作流
- `/checkpoint` - 通用检查点
- `/context-archive` - 归档上下文
