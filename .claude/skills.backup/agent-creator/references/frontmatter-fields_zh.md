# Agent Frontmatter字段参考

本文档提供创建Claude Code子代理时所有可用YAML frontmatter字段的完整参考。

## 必需字段

### name
- **类型**：字符串
- **必需**：是
- **描述**：agent的唯一标识符，使用小写字母和连字符
- **示例**：`code-reviewer`、`test-runner`、`data-scientist`
- **规则**：
  - 仅使用小写字母
  - 用连字符分隔单词
  - 在作用域内必须唯一
  - 应该描述性且简洁

### description
- **类型**：字符串
- **必需**：是
- **描述**：定义Claude何时应该委派给此子代理。这是主要的触发机制。
- **最佳实践**：
  - 包含agent做什么和何时使用
  - 添加"主动使用"以鼓励自动委派
  - 对触发条件要具体
  - 在这里包含所有"何时使用"信息（不在正文中）
- **示例**：
  ```yaml
  description: 专业代码审查专家。主动审查代码的质量、安全性和可维护性。在编写或修改代码后立即使用。
  ```

## 可选字段

### tools
- **类型**：字符串或数组
- **必需**：否
- **默认值**：从主对话继承所有工具
- **描述**：指定子代理可以使用哪些工具（白名单）
- **可用工具**：Read、Write、Edit、Bash、Grep、Glob、Task和任何MCP工具
- **示例**：
  ```yaml
  # 字符串格式（逗号分隔）
  tools: Read, Grep, Glob, Bash

  # 数组格式
  tools:
    - Read
    - Grep
    - Glob
    - Bash
  ```
- **特殊值**：
  - 省略字段以继承所有工具
  - 在/agents UI中使用"Read-only tools"选择只读子集

### disallowedTools
- **类型**：字符串或数组
- **必需**：否
- **描述**：要拒绝的工具，从继承或指定的列表中删除（黑名单）
- **用例**：当你想要大多数工具但需要阻止特定工具时
- **示例**：
  ```yaml
  tools: Read, Grep, Glob, Bash, Write, Edit
  disallowedTools: Write, Edit
  # 结果：Agent只能使用Read、Grep、Glob、Bash
  ```

### model
- **类型**：字符串
- **必需**：否
- **默认值**：`inherit`（使用与主对话相同的模型）
- **描述**：指定子代理使用哪个AI模型
- **有效值**：
  - `sonnet` - 最适合复杂编码任务、分析
  - `opus` - 最深推理、架构决策
  - `haiku` - 快速、经济，适合简单任务
  - `inherit` - 使用与父对话相同的模型
- **选择指南**：
  - 使用`haiku`：简单搜索、测试运行、快速检查
  - 使用`sonnet`：代码审查、调试、实现
  - 使用`opus`：复杂架构决策、深度分析
  - 使用`inherit`：当模型选择无关紧要时
- **示例**：
  ```yaml
  model: sonnet
  ```

### permissionMode
- **类型**：字符串
- **必需**：否
- **默认值**：从父对话继承
- **描述**：控制子代理如何处理权限提示
- **有效值**：
  - `default` - 标准权限检查和提示
  - `acceptEdits` - 自动接受文件编辑
  - `dontAsk` - 自动拒绝权限提示（明确允许的工具仍然有效）
  - `bypassPermissions` - 跳过所有权限检查（⚠️ 谨慎使用）
  - `plan` - 计划模式（只读探索）
- **警告**：`bypassPermissions`跳过所有权限检查。仅在绝对必要时使用。
- **示例**：
  ```yaml
  permissionMode: acceptEdits
  ```

### skills
- **类型**：数组
- **必需**：否
- **描述**：在启动时加载到子代理上下文中的skills。完整的skill内容被注入，而不仅仅是可供调用。
- **重要**：子代理不从父对话继承skills；你必须明确列出它们。
- **示例**：
  ```yaml
  skills:
    - api-conventions
    - error-handling-patterns
    - testing-best-practices
  ```
- **用例**：当子代理需要领域知识或约定来执行其任务时

### hooks
- **类型**：对象
- **必需**：否
- **描述**：作用域限定于此子代理的生命周期hooks。Hooks仅在子代理活动时运行。
- **支持的事件**：
  - `PreToolUse` - 在子代理使用工具之前
  - `PostToolUse` - 在子代理使用工具之后
  - `Stop` - 当子代理完成时（在运行时转换为SubagentStop）
- **结构**：
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
- **用例**：
  - 在执行前验证工具输入
  - 在文件修改后运行自动检查
  - 对工具使用强制约束
  - 添加日志或监控

## 完整示例

```yaml
---
name: api-developer
description: 遵循团队约定实现API端点。在创建或修改API路由时主动使用。
tools: Read, Write, Edit, Bash, Grep, Glob
disallowedTools: Task
model: sonnet
permissionMode: acceptEdits
skills:
  - api-conventions
  - error-handling-patterns
hooks:
  PostToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: command
          command: "./scripts/format-code.sh"
---

你是一位API开发专家...
```

## 字段验证规则

1. **name**：必须仅使用小写字母和连字符
2. **description**：必须非空且具有描述性
3. **tools**：必须引用有效的工具名称
4. **model**：必须是以下之一：sonnet、opus、haiku、inherit
5. **permissionMode**：必须是以下之一：default、acceptEdits、dontAsk、bypassPermissions、plan
6. **skills**：必须引用现有的skill名称
7. **hooks**：必须遵循正确的hook结构，具有有效的事件和匹配器

## 常见模式

### 只读Agent
```yaml
tools: Read, Grep, Glob, Bash
disallowedTools: Write, Edit
```

### 快速、经济的Agent
```yaml
model: haiku
tools: Read, Bash
```

### 带验证的安全Agent
```yaml
tools: Bash
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-command.sh"
```

### 领域特定Agent
```yaml
model: sonnet
skills:
  - domain-knowledge
  - team-conventions
permissionMode: acceptEdits
```
