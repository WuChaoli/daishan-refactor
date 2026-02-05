# Agent创建最佳实践

本文档提供创建有效Claude Code子代理的指南和最佳实践。

## 设计原则

### 1. 单一职责
每个agent应该擅长一项特定任务。不要创建"无所不能"的agents。

**好的**：
- `code-reviewer` - 审查代码质量
- `test-runner` - 运行测试并报告失败
- `debugger` - 诊断和修复bug

**不好的**：
- `developer-helper` - 做代码审查、测试、调试和部署

### 2. 清晰的触发条件
编写清楚指示Claude何时应该使用agent的描述。

**好的**：
```yaml
description: 专业代码审查专家。主动审查代码的质量、安全性和可维护性。在编写或修改代码后立即使用。
```

**不好的**：
```yaml
description: 审查代码
```

### 3. 适当的工具访问
仅授予agent任务所需的工具。这提高了安全性和专注度。

**只读任务**（代码审查、分析）：
```yaml
tools: Read, Grep, Glob, Bash
```

**修改任务**（调试、重构）：
```yaml
tools: Read, Edit, Bash, Grep, Glob
```

**创建任务**（脚手架、生成）：
```yaml
tools: Read, Write, Bash, Grep, Glob
```

### 4. 模型选择策略
根据任务复杂度和频率选择合适的模型。

- **Haiku**：简单、频繁的任务（测试运行、文件搜索、快速检查）
- **Sonnet**：复杂分析和实现（代码审查、调试、功能开发）
- **Opus**：深度推理和架构（系统设计、复杂重构）
- **Inherit**：当模型选择不会显著影响结果时

## 描述编写指南

`description`字段是Claude决定何时使用你的agent的主要方式。遵循这些指南：

### 包含"主动使用"
鼓励Claude自动使用agent：
```yaml
description: 在代码更改后主动使用以运行测试并报告失败。
```

### 指定触发上下文
列出应该使用agent的具体情况：
```yaml
description: 调试专家，用于错误、测试失败和意外行为。在遇到任何问题时主动使用。
```

### 结合"做什么"和"何时用"
描述agent的能力和何时使用：
```yaml
description: 数据分析专家，用于SQL查询、BigQuery操作和数据洞察。主动用于数据分析任务和查询。
```

### 要避免的不好示例
- 太模糊："帮助编码"
- 缺少触发器："专业代码审查员"（何时应该使用？）
- 太窄："审查src/目录中的Python文件"（过于具体）

## 系统提示最佳实践

markdown正文成为agent的系统提示。使其可操作且结构化。

### 1. 从角色定义开始
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

## 常见模式

### 模式1：只读分析器
**用例**：代码审查、安全审计、文档分析

```yaml
---
name: analyzer-name
description: [它分析什么]。在[何时使用]时主动使用。
tools: Read, Grep, Glob, Bash
model: sonnet
---

你是[领域]专家。

被调用时：
1. [步骤1]
2. [步骤2]
3. [步骤3]

分析清单：
- [项目1]
- [项目2]

按[标准]提供组织的结果。
```

### 模式2：修改器Agent
**用例**：调试、重构、代码生成

```yaml
---
name: modifier-name
description: [它修改什么]。在[何时使用]时主动使用。
tools: Read, Edit, Bash, Grep, Glob
model: sonnet
---

你是[领域]专家。

被调用时：
1. 分析当前状态
2. 识别需要更改的内容
3. 实施最小修复
4. 验证解决方案有效

对于每次更改，提供：
- 问题解释
- 应用的具体修复
- 测试方法
```

### 模式3：验证工具使用
**用例**：数据库查询、API调用、系统命令

```yaml
---
name: validated-agent
description: [它做什么并进行验证]。在[上下文]时使用。
tools: Bash
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-command.sh"
---

你是具有[约束]的[角色]。

被要求[任务]时：
1. [步骤1]
2. [步骤2]
3. [步骤3]

你不能[禁止的操作]。如果被要求，请解释限制。
```

### 模式4：领域专家
**用例**：数据分析、API开发、基础设施

```yaml
---
name: specialist-name
description: [领域]专家，用于[特定任务]。主动用于[上下文]。
tools: [适当的工具]
model: sonnet
skills:
  - domain-knowledge
  - team-conventions
---

你是[领域]专家。

被调用时：
1. 理解[领域特定]需求
2. 应用[领域]最佳实践
3. [领域特定操作]

关键实践：
- [实践1]
- [实践2]

对于每个[输出]：
- [要求1]
- [要求2]
```

## 上下文管理

### 隔离高容量操作
使用agents将详细输出排除在主对话之外：
```yaml
description: 使用子代理运行测试套件，仅报告失败的测试及其错误消息
```

### 返回摘要，而非原始数据
指示agents总结结果：
```markdown
将详细的测试输出保留在你的上下文中。仅返回：
- 通过/失败计数摘要
- 失败测试的详细信息
- 相关错误消息
```

## 权限管理

### 默认模式
标准权限检查。适合大多数agents：
```yaml
permissionMode: default
```

### 接受编辑
为受信任的修改agents自动接受文件编辑：
```yaml
permissionMode: acceptEdits
```

### 不询问
自动拒绝提示但允许明确授予的工具：
```yaml
permissionMode: dontAsk
tools: Read, Bash
```

### 绕过权限（⚠️ 危险）
仅用于完全受信任、经过充分测试的agents：
```yaml
permissionMode: bypassPermissions  # 极其谨慎使用
```

## 高级控制的Hooks

### 验证输入
```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-bash-command.sh"
```

### 后处理输出
```yaml
hooks:
  PostToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: command
          command: "./scripts/format-and-lint.sh"
```

### 完成时清理
```yaml
hooks:
  Stop:
    - hooks:
        - type: command
          command: "./scripts/cleanup-temp-files.sh"
```

## 测试你的Agent

### 1. 使用显式调用测试
```
使用[agent-name] agent执行[任务]
```

### 2. 测试自动委派
描述应该触发agent的任务而不命名它：
```
审查我刚写的代码是否存在安全问题
```

### 3. 测试工具限制
尝试让agent使用不允许的工具：
```
使用code-reviewer agent修复它发现的问题
```
（如果code-reviewer是只读的，应该失败）

### 4. 测试边缘情况
- 空输入
- 大文件
- 多个同时请求
- 权限拒绝

## 要避免的常见错误

### 1. 过于宽泛的描述
**不好的**："帮助开发任务"
**好的**："调试专家，用于错误、测试失败和意外行为。在遇到任何问题时主动使用。"

### 2. 太多工具
**不好的**：当只需要Read时授予所有工具
**好的**：仅授予任务所需的工具

### 3. 缺少工作流程
**不好的**："你是一位代码审查员。"
**好的**：提供逐步工作流程和检查清单

### 4. 模糊的输出要求
**不好的**："提供反馈"
**好的**："按优先级提供反馈：关键、警告、建议。包含具体示例。"

### 5. 无边界
**不好的**：不指定agent不能做什么
**好的**："你不能修改数据。如果被要求INSERT、UPDATE、DELETE，请解释你只有读取权限。"

## 作用域选择

### 用户级Agents（~/.claude/agents/）
用于你想在所有项目中使用的个人agents：
- 个人代码审查偏好
- 自定义分析工具
- 工作流助手

### 项目级Agents（.claude/agents/）
用于团队共享的项目特定agents：
- 项目特定约定
- 代码库的领域知识
- 团队工作流程

将项目agents检入版本控制，以便团队可以协作改进。

### 插件Agents
用于可分发、可重用的agents：
- 通用工具
- 框架特定助手
- 行业标准工作流程

## 性能优化

### 对简单任务使用Haiku
```yaml
model: haiku  # 对简单操作节省3倍成本
```

### 通过工具限制限制上下文
```yaml
tools: Read, Bash  # 更少的工具=更简单的决策
```

### 为领域知识预加载Skills
```yaml
skills:
  - api-conventions  # 在启动时注入知识
```

### 为独立工作在后台运行
```
在后台运行test-runner agent
```

## 维护

### 版本控制
- 将项目agents检入git
- 在提交消息中记录更改
- 定期审查agent有效性

### 迭代
- 监控哪些agents被频繁使用
- 根据使用模式优化描述
- 随着需求演变更新系统提示

### 清理
- 删除未使用的agents
- 合并相似的agents
- 归档过时的agents

## 安全考虑

### 最小权限原则
仅授予必要的工具：
```yaml
tools: Read, Grep, Glob  # 无Write、Edit或Bash
```

### 验证危险操作
使用hooks验证风险命令：
```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-command.sh"
```

### 避免bypassPermissions
仅在绝对必要且经过充分测试时使用。

### 审查Hook脚本
确保验证脚本安全且正确。

## 总结检查清单

创建agent时，确保：
- [ ] 名称具有描述性并使用小写-连字符
- [ ] 描述包含它做什么和何时使用
- [ ] 描述包含"主动使用"（如果适用）
- [ ] 工具限制为必要的
- [ ] 模型适合任务复杂度
- [ ] 系统提示提供清晰的工作流程
- [ ] 系统提示指定输出格式
- [ ] 系统提示设定边界
- [ ] 使用显式和自动调用测试
- [ ] 为团队成员记录（如果是项目级）
