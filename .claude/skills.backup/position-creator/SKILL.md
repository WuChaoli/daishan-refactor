---
name: position-creator
description: 为公司职位创建职位模板。当用户提到"创建职位模板"、"生成职位模板"、"定义职位"、"position template"或需要为架构师、产品经理、开发者等职位创建标准化职位定义时使用。创建的模板文件控制在800字以内。
---

# 职位模板创建器

## 概述

为公司职位创建标准化的职位模板。职位模板定义了职位的职责、工具、技能、文档产出和工作规则，存储在 `company/position/` 目录。

创建员工时，从模板库复制到 `company/employee/` 目录。

## 工作流程

### 1. 收集职位信息

**必需信息**：
- 职位名称（如：资深架构师、产品经理、全栈开发工程师）
- 所属部门（如：技术部、产品部）
- 核心职责（3-5条）

**可选信息**：
- 次要职责（2-3条）
- 需要的工具
- 需要的技能
- 产出的文档类型
- 特殊规则

**提问示例**：
```
请告诉我：
1. 职位名称？
2. 所属部门？
3. 核心职责是什么？
4. 需要哪些工具？（Read、Write、Bash等）
5. 需要哪些技能？（tdd-workflow、c4-architecture等）
6. 产出哪些文档？
7. 有什么特殊工作规则？
```

### 2. 读取模板和参考资料

读取以下文件：

1. **职位模板**：`${CLAUDE_SKILL_ROOT}/assets/position-template.md`
   - 简化的模板结构
   - 直接复制并定制

2. **组件说明**：`${CLAUDE_SKILL_ROOT}/references/position-components.md`
   - 各部分的编写指导

3. **示例职位**：`${CLAUDE_SKILL_ROOT}/references/examples.md`
   - 完整的职位模板示例

### 3. 定制职位模板

**模板结构**（800字以内）：

```yaml
---
role: [role-name]
position: [position-title]
department: [department-name]
version: 1.0.0
created: [YYYY-MM-DD]
updated: [YYYY-MM-DD]
---

# [职位名称] 职位模板

## 概述
[1-2句话描述角色定位和核心价值]

## 职责
### 核心职责
- [核心职责1]
- [核心职责2]
- [核心职责3]

### 次要职责
- [次要职责1]
- [次要职责2]

## 工具
**必需工具**: Read, Write, [其他]
**可选工具**: Bash, Grep, Glob, [其他]

## 技能
**固定加载**: context-manage
**角色专属**: [技能1], [技能2]

## 可用Agents
**推荐使用**:
- **[agent1]**: [用途说明]
- **[agent2]**: [用途说明]
- **[agent3]**: [用途说明]

## 文档产出
| 文档名称 | 位置 | 用途 | 更新频率 |
|---------|------|------|---------|
| [文档1] | [路径] | [用途] | [频率] |

## 工作规则
1. [规则1]
2. [规则2]
3. [规则3]
4. [规则4]

## 工作流程
### 标准流程
1. **[步骤1]**: [说明]
2. **[步骤2]**: [说明]
3. **[步骤3]**: [说明]

### 特殊场景
- **[场景1]**: [处理方式]
- **[场景2]**: [处理方式]

## 质量检查
- [ ] [检查项1]
- [ ] [检查项2]
- [ ] [检查项3]
- [ ] [检查项4]

## 协作接口
### 与[角色A]协作
- **场景**: [协作场景]
- **交接**: [交接文档]
```

### 4. 创建职位文件

**文件位置**：`company/position/[role-name].md`

**操作**：
```bash
# 确保目录存在
mkdir -p company/position

# 创建职位文件
# 使用Write工具创建文件
```

### 5. 验证字数和内容

**字数检查**：
```bash
wc -w company/position/[role-name].md
```

**验证清单**：
- [ ] 总字数在800字以内
- [ ] YAML frontmatter格式正确
- [ ] 包含context-manage技能
- [ ] 职责清晰具体（3-5条核心职责）
- [ ] 工具列表完整
- [ ] 工作规则可执行
- [ ] 文档路径明确

## 简洁化原则

### 0. 文档路径设计最佳实践

**根目录概念**：
- 明确说明根目录：`docs/contexts/YYYY-MM-DD_feature/`
- 表格中只写相对路径，避免重复

**子目录组织**：
- 按职位/任务类型创建子目录（如：`refactor/`, `testing/`, `arch/`, `dev/`）
- 避免不同职位的文档混在一起

**任务目录命名**：
- 格式：`DD-HHMM_<task_brief_name>/`
- 使用时间戳+任务简述
- 避免文档覆盖

**完整示例**：
```
docs/contexts/YYYY-MM-DD_feature/
├── requirements.md              # 功能级文档
├── refactor/                    # 重构任务
│   └── DD-HHMM_<task_name>/
│       ├── tests/              # 测试代码
│       ├── baseline.md
│       └── summary.md
├── testing/                     # 测试任务
│   └── DD-HHMM_<test_desc>/
│       ├── test-cases.md
│       └── execution-log.md
└── arch/                        # 架构任务
    └── DD-HHMM_<arch_task>/
        ├── design.md
        └── diff.md
```

**文档产出部分写法**：
```markdown
## 文档产出

**根目录**: `docs/contexts/YYYY-MM-DD_feature/`

所有[职位]相关文档统一放在子目录 `[subdir]/DD-HHMM_<task_brief_name>/` 下：

| 文档名称 | 位置 | 用途 | 更新频率 |
|---------|------|------|---------|
| [文档1] | `[subdir]/DD-HHMM_<task_name>/file1.md` | [用途] | [频率] |
| [文档2] | `[subdir]/DD-HHMM_<task_name>/file2.md` | [用途] | [频率] |

**目录结构示例**:
\```
docs/contexts/YYYY-MM-DD_feature/
└── [subdir]/
    └── DD-HHMM_<task_name>/
        ├── file1.md
        └── file2.md
\```
```

### 1. 概述精简
- 1-2句话概括核心价值
- 不超过30字

### 2. 职责精简
- 核心职责：3-5条，每条一句话
- 次要职责：2-3条，每条一句话
- 使用动词开头

### 3. 工具列表
- 必需工具和可选工具分组
- 只列工具名，不添加说明

### 4. 技能列表
- 固定加载：只列context-manage
- 角色专属：2-4个技能名称

### 5. Agents列表
- 推荐使用：2-4个agents
- 简短说明用途

### 6. 文档产出
- 明确根目录：`docs/contexts/YYYY-MM-DD_feature/`
- 按职位类型创建子目录（如：`refactor/`, `testing/`, `arch/`）
- 任务目录命名：`DD-HHMM_<task_brief_name>/`
- 表格中只写相对路径
- 添加目录结构示例
- 只列核心文档（3-6个）
- 简短说明用途和频率

### 7. 工作规则
- 4条核心规则
- 每条一句话，具体可执行

### 8. 工作流程
- 标准流程：4-6步
- 每步一句话说明
- 特殊场景：2-3个

### 9. 质量检查
- 4-6项检查项
- 简短具体

### 10. 协作接口
- 只列主要协作角色
- 简短说明协作场景

## 可用工具列表

### 文件操作
- **Read**: 读取文件内容
- **Write**: 创建新文件
- **Edit**: 修改现有文件
- **Glob**: 查找文件
- **Grep**: 搜索内容

### 命令执行
- **Bash**: 运行Shell命令

### 高级功能
- **Task**: 启动子agent
- **AskUserQuestion**: 提问
- **TodoWrite**: 任务管理

## 可用技能列表

### 必需技能
- **context-manage**: 上下文管理（所有职位必需）

### 开发相关
- **tdd-workflow**: TDD开发流程
- **code-review**: 代码审查
- **commit**: Git提交规范

### 架构设计
- **c4-architecture**: C4架构图
- **mermaid-diagrams**: 图表绘制

### 产品管理
- **code-new-requirement**: 需求分析

### 文档管理
- **context-engineering**: 上下文工程
- **context-init**: 初始化上下文
- **context-archive**: 归档上下文

## 字数分配建议

总字数控制在800字以内：

- YAML frontmatter: ~50字
- 概述: ~30字
- 职责: ~100字
- 工具: ~50字
- 技能: ~40字
- 文档产出: ~120字
- 工作规则: ~80字
- 工作流程: ~150字
- 质量检查: ~60字
- 协作接口: ~80字
- 其他: ~40字
- **总计**: ~800字

## 快速开始

创建新职位模板：

1. 调用 `/position-creator`
2. 回答关于职位的问题
3. 查看生成的模板
4. 验证字数在800字以内
5. 保存到 `company/position/[role-name].md`

## 后续使用

创建职位模板后：

1. **创建员工**: 使用 `/hire-employee` 从模板创建员工
2. **更新模板**: 定期更新模板以反映变化
3. **版本管理**: 使用语义化版本号

## 注意事项

1. **字数限制**: 职位模板必须在800字以内
2. **context-manage必需**: 所有职位模板都必须包含
3. **文档路径规范**: 使用相对路径
4. **规则可执行性**: 规则要具体可执行
5. **模板复用**: 创建员工时从模板复制

## 相关资源

- **职位模板**: `${CLAUDE_SKILL_ROOT}/assets/position-template.md`
- **组件说明**: `${CLAUDE_SKILL_ROOT}/references/position-components.md`
- **示例职位**: `${CLAUDE_SKILL_ROOT}/references/examples.md`
- **招聘员工**: `/hire-employee`
- **上下文工程**: `.claude/rules/context-engineering.md`

---

**版本**: 2.0.0 | **更新**: 2026-02-02
**重命名自**: role-template-creator
