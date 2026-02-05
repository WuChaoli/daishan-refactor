---
name: agent-creator
description: 创建Claude Code子代理（自定义AI助手）的综合指南。当用户想要创建agents、subagents、自定义agents、专用agents，或询问"如何创建agent"、"构建subagent"、"制作自定义agent"，或提到agent创建、agent开发或使用agents扩展Claude时使用。
---

# Agent创建器

创建专门的AI子代理，用于处理特定任务，具有自定义系统提示、工具访问权限和权限设置。

## 什么是子代理？

子代理是专门的AI助手，在自己的上下文窗口中运行，具有：
- **自定义系统提示**：针对特定领域
- **特定工具访问**：可以限制
- **独立权限**：可以更宽松或更严格
- **独立上下文**：将探索性操作与主对话分离

### 子代理的优势

- **保留上下文**：将冗长的操作排除在主对话之外
- **强制约束**：限制子代理可以使用的工具
- **重用配置**：在项目间共享agents
- **专业化行为**：专注于特定领域或任务
- **控制成本**：将任务路由到更快、更便宜的模型如Haiku

## 快速开始

### 使用/agents命令（推荐）

创建agent的最简单方法：

1. 在Claude Code中运行`/agents`
2. 选择"Create new agent"
3. 选择作用域（User-level或Project-level）
4. 使用Claude生成或手动创建
5. 配置工具和模型
6. 保存并立即使用

### 手动创建

创建带有YAML frontmatter的Markdown文件：

```markdown
---
name: agent-name
description: 它做什么。在[上下文]时主动使用。
tools: Read, Grep, Glob, Bash
model: sonnet
---

你是[角色]。

被调用时：
1. [步骤1]
2. [步骤2]
3. [步骤3]
```

保存到：
- `~/.claude/agents/` 用于用户级（所有项目）
- `.claude/agents/` 用于项目级（当前项目）

## Agent结构

### 必需：YAML Frontmatter

两个必需字段：

**name**：唯一标识符（小写-连字符）
```yaml
name: code-reviewer
```

**description**：Claude何时应该使用此agent（主要触发器）
```yaml
description: 专业代码审查专家。主动审查代码的质量、安全性和可维护性。在编写或修改代码后立即使用。
```

### 必需：系统提示（Markdown正文）

frontmatter之后的markdown内容成为agent的系统提示：

```markdown
你是一位资深代码审查员。

被调用时：
1. 运行git diff查看最近的更改
2. 专注于修改的文件
3. 立即开始审查

审查清单：
- 代码清晰易读
- 正确的错误处理
- 无安全漏洞
```

## 配置选项

### 工具

控制agent可以使用哪些工具：

```yaml
# 仅允许特定工具
tools: Read, Grep, Glob, Bash

# 或允许所有工具除了特定工具
tools: Read, Write, Edit, Bash, Grep, Glob
disallowedTools: Write, Edit
```

**常见模式**：
- 只读：`Read, Grep, Glob, Bash`
- 修改器：`Read, Edit, Bash, Grep, Glob`
- 创建器：`Read, Write, Bash, Grep, Glob`

### 模型选择

为任务选择合适的模型：

```yaml
model: sonnet  # 或：haiku, opus, inherit
```

- **haiku**：快速、经济（简单搜索、测试运行）
- **sonnet**：平衡（代码审查、调试、实现）
- **opus**：深度推理（架构、复杂分析）
- **inherit**：使用与主对话相同的模型

### 权限模式

```yaml
permissionMode: default  # 或：acceptEdits, dontAsk, bypassPermissions, plan
```

- **default**：标准权限提示
- **acceptEdits**：自动接受文件编辑
- **dontAsk**：自动拒绝提示（允许的工具仍然有效）
- **bypassPermissions**：跳过所有检查（⚠️ 谨慎使用）
- **plan**：只读探索模式

### Skills

在启动时将skill内容注入agent的上下文：

```yaml
skills:
  - api-conventions
  - error-handling-patterns
```

### Hooks

添加生命周期hooks用于验证或自动化：

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-command.sh"
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "./scripts/run-linter.sh"
```

## 编写有效的描述

`description`字段是Claude决定何时使用你的agent的方式。使其清晰具体。

### 包含"主动使用"

鼓励自动委派：
```yaml
description: 在代码更改后主动使用以运行测试并报告失败。
```

### 指定触发上下文

列出何时应该使用agent：
```yaml
description: 调试专家，用于错误、测试失败和意外行为。在遇到任何问题时主动使用。
```

### 结合"做什么"和"何时用"

```yaml
description: 数据分析专家，用于SQL查询、BigQuery操作和数据洞察。主动用于数据分析任务和查询。
```

## 编写系统提示

markdown正文指导agent的行为。使其可操作。

### 1. 定义角色

```markdown
你是一位资深代码审查员，确保高标准的代码质量和安全性。
```

### 2. 提供清晰的工作流程

```markdown
被调用时：
1. 运行git diff查看最近的更改
2. 专注于修改的文件
3. 立即开始审查
```

### 3. 包含检查清单

```markdown
审查清单：
- 代码清晰易读
- 函数和变量命名良好
- 无重复代码
- 正确的错误处理
```

### 4. 指定输出格式

```markdown
按优先级提供反馈：
- 关键问题（必须修复）
- 警告（应该修复）
- 建议（考虑改进）

包含如何修复问题的具体示例。
```

### 5. 设定边界

```markdown
你不能修改数据。如果被要求INSERT、UPDATE、DELETE或修改架构，请解释你只有读取权限。
```

## 常见Agent模式

### 只读分析器

用于代码审查、安全审计、分析：

```yaml
---
name: code-reviewer
description: 专业代码审查专家。在编写或修改代码后主动使用。
tools: Read, Grep, Glob, Bash
model: sonnet
---

你是一位资深代码审查员。

被调用时：
1. 运行git diff查看最近的更改
2. 专注于修改的文件
3. 立即开始审查

审查清单：
- 代码质量
- 安全问题
- 最佳实践

按优先级提供反馈：关键、警告、建议。
```

### 修改器Agent

用于调试、重构、代码生成：

```yaml
---
name: debugger
description: 调试专家。在遇到错误或测试失败时主动使用。
tools: Read, Edit, Bash, Grep, Glob
model: sonnet
---

你是一位专业调试专家。

被调用时：
1. 捕获错误消息和堆栈跟踪
2. 识别重现步骤
3. 隔离失败位置
4. 实施最小修复
5. 验证解决方案有效
```

### 验证工具使用

用于数据库查询、带约束的API调用：

```yaml
---
name: db-reader
description: 执行只读数据库查询。在分析数据或生成报告时使用。
tools: Bash
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-readonly-query.sh"
---

你是一位具有只读访问权限的数据库分析师。

执行SELECT查询以回答有关数据的问题。
你不能修改数据。如果被要求INSERT、UPDATE、DELETE，请解释你只有读取权限。
```

### 领域专家

用于数据分析、API开发、基础设施：

```yaml
---
name: data-scientist
description: 数据分析专家，用于SQL查询和BigQuery操作。主动用于数据分析任务。
tools: Bash, Read, Write
model: sonnet
skills:
  - sql-conventions
  - data-analysis-patterns
---

你是一位专门从事SQL和BigQuery分析的数据科学家。

被调用时：
1. 理解数据分析需求
2. 编写高效的SQL查询
3. 分析和总结结果
4. 清晰地呈现发现
```

## Agent作用域

### 用户级（~/.claude/agents/）

在所有项目中可用的个人agents：
- 个人代码审查偏好
- 自定义分析工具
- 工作流助手

### 项目级（.claude/agents/）

团队共享的项目特定agents：
- 项目约定
- 代码库的领域知识
- 团队工作流程

**最佳实践**：将项目agents检入版本控制，以便团队协作。

### 插件Agents

可分发、可重用的agents：
- 通用工具
- 框架特定助手
- 行业标准工作流程

## 使用Agents

### 自动委派

Claude根据描述自动委派：
```
审查我刚写的代码
```
（如果描述匹配，则触发code-reviewer agent）

### 显式调用

请求特定agent：
```
使用test-runner agent修复失败的测试
让code-reviewer agent查看我最近的更改
```

### 后台执行

并发运行agents：
```
在后台运行test-runner agent
```

## 最佳实践

### 设计原则

1. **单一职责**：每个agent擅长一项特定任务
2. **清晰触发器**：描述清楚地指示何时使用
3. **适当工具**：仅授予必要的权限
4. **结构化工作流程**：提供逐步过程
5. **质量输出**：指定结果的格式和内容

### 描述指南

- 包含"主动使用"以鼓励自动委派
- 清楚地指定触发上下文
- 结合agent做什么和何时使用
- 避免模糊描述如"帮助编码"

### 系统提示指南

- 从角色定义开始
- 提供清晰的工作流程步骤
- 包含检查清单以保持一致性
- 指定输出格式
- 设定agent不能做什么的边界

### 工具选择

- **只读任务**：`Read, Grep, Glob, Bash`
- **修改任务**：`Read, Edit, Bash, Grep, Glob`
- **创建任务**：`Read, Write, Bash, Grep, Glob`

### 模型选择

- **Haiku**：简单、频繁的任务（节省3倍成本）
- **Sonnet**：复杂分析和实现
- **Opus**：深度推理和架构
- **Inherit**：当模型选择无关紧要时

## 高级功能

### 用于验证的Hooks

在执行前验证工具输入：

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-command.sh"
```

验证脚本通过stdin接收JSON，可以通过退出代码2阻止执行。

### 用于领域知识的Skills

将skills预加载到agent上下文：

```yaml
skills:
  - api-conventions
  - error-handling-patterns
```

完整的skill内容在启动时注入，而不仅仅是可供调用。

### 链式Agents

按顺序使用agents：
```
使用code-reviewer agent查找性能问题，然后使用optimizer agent修复它们
```

### 并行研究

为独立调查生成多个agents：
```
使用单独的agents并行研究身份验证、数据库和API模块
```

## 参考文档

详细信息请参见：

- **[agent-examples.md](references/agent-examples.md)**：来自Claude Code文档的完整示例agents
- **[frontmatter-fields.md](references/frontmatter-fields.md)**：所有可用的YAML frontmatter字段
- **[best-practices.md](references/best-practices.md)**：综合指南和模式

## 模板

使用此模板开始创建你的agent：

```markdown
---
name: agent-name
description: [此agent做什么]。在[何时使用]时主动使用。
tools: Read, Grep, Glob, Bash
model: inherit
---

你是[角色描述]。

被调用时：
1. [第一步]
2. [第二步]
3. [第三步]

[任务特定部分]：
- [项目1]
- [项目2]
- [项目3]

提供[输出格式]：
- [要求1]
- [要求2]
- [要求3]

[附加说明或约束]
```

模板文件也可在[assets/agent-template.md](assets/agent-template.md)获取。

## 测试你的Agent

1. **测试显式调用**：`使用[agent-name] agent执行[任务]`
2. **测试自动委派**：描述任务而不命名agent
3. **测试工具限制**：尝试让agent使用不允许的工具
4. **测试边缘情况**：空输入、大文件、权限拒绝

## 要避免的常见错误

1. **过于宽泛的描述**：具体说明何时使用
2. **太多工具**：仅授予必要的
3. **缺少工作流程**：提供逐步说明
4. **模糊的输出要求**：清楚地指定格式
5. **无边界**：说明agent不能做什么

## 故障排除

### Agent未触发

- 检查描述是否清晰具体
- 在描述中添加"主动使用"
- 首先尝试显式调用
- 如果agent刚创建，重启会话

### 权限问题

- 检查permissionMode设置
- 验证工具是否正确指定
- 查看disallowedTools列表
- 首先使用显式权限测试

### 意外行为

- 检查系统提示的清晰度
- 检查工具限制
- 验证hooks是否正常工作
- 使用更简单的任务测试

## 下一步

创建agent后：

1. 使用显式调用测试
2. 测试自动委派
3. 根据使用情况优化描述
4. 与团队共享（如果是项目级）
5. 记录任何特殊要求
6. 根据反馈迭代

有关更多示例和模式，请参见`references/`目录中的参考文档。
