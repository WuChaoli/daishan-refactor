---
name: serena-mcp
description: AI 编码代理工具包，通过 LSP 符号级理解能力提供项目分析、代码导航、智能重构和错误诊断。使用场景：(1) 需要深入理解代码库结构时，如"分析项目架构"、"找出所有调用某函数的地方" (2) 进行符号级编辑而非文本替换时，如"重构这个函数" (3) 需要项目记忆和上下文延续时 (4) 想要避免基于文本搜索的 RAG 局限时。Serena 提供 IDE 级别的符号搜索、符号后插入、替换符号体等工具。
---

# Serena MCP - AI 编码代理工具包

## 概述

Serena 是一款通过 LSP (Language Server Protocol) 提供符号级理解能力的 AI 编码代理工具包。与传统基于文本搜索的方法不同，Serena 能够准确理解代码结构、符号定义和引用关系，特别适合复杂代码库的深度分析。

## 核心能力

### 1. 项目激活与索引

在使用任何 Serena 工具之前，必须先激活项目：

**通过 MCP 工具激活**：
- Claude Code 会自动调用 Serena MCP 的 `activate_project` 工具
- 无需手动设置环境变量或运行命令

**最佳实践：**
- 大型项目建议先建立索引以加速工具运行
- Serena 同时只能处理一个项目
- 激活后，Serena 会执行入职流程 (onboarding)，分析项目结构并存储记忆到 `.serena/memories/`

### 2. 项目入职与记忆系统

**首次使用：** Serena 自动执行入职流程，分析：
- 项目结构和技术栈
- 关键业务逻辑
- 重要架构决策

**记忆利用：**
- 入职信息存储在 `.serena/memories/` 目录
- 跨对话维持上下文
- 后续对话可选择性读取记忆文件

**绕过入职：** 在 `.serena/memories/` 中创建任意文件即可跳过入职流程。

### 3. 核心工作流

#### 符号级导航

**使用场景：**
- "找出所有调用 UserService 的地方"
- "显示这个函数的完整定义"
- "查找这个类的所有子类"

**MCP 工具：** Serena 提供的符号查找工具用于通过符号名精确定位定义和引用

#### 符号级编辑

**核心操作：** Serena MCP 提供 `replace_symbol_body` 工具用于替换符号的完整主体

**优势：**
- 比文本替换更准确
- 保持代码结构完整性
- 避免误改相似代码

**示例工具：**
- `insert_after_symbol` - 在符号后插入代码
- `replace_symbol_body` - 替换整个函数/类实现

#### 智能重构

**典型任务：**
- "重构这个函数，提取公共逻辑"
- "确保符合项目现有代码风格"
- "优化这段代码的性能"

**最佳实践：**
- 启用 `execute_shell_command` 工具（默认启用）
- 允许 Serena 自主运行测试并纠错
- 查看 `.serena/memories/` 了解项目风格

#### 错误诊断

**诊断类型：**
- 潜在 Bug 检测
- 内存泄漏检查
- 代码异味识别
- 安全漏洞扫描

#### 上下文管理

**上下文管理：**

当对话接近上下文限制时，使用 Serena MCP 提供的 `prepare_for_new_conversation` 工具：

1. 创建当前状态摘要
2. 保存为记忆文件
3. 在新对话中读取该记忆以继续工作

## 模式和上下文定制

### 上下文 (Contexts)

在启动时设置，定义操作环境：

- **`desktop-app`** (默认): Claude Desktop 应用环境
- **`agent`**: 更自主的代理模式
- **`ide`**: IDE 集成模式（推荐用于 VSCode、JetBrains 等 IDE）
- **`claude-code`**: Claude Code CLI 专用上下文，禁用重复工具
- **`codex`**: Codex CLI 专用上下文（Codex 不完全支持 MCP 规范）

**推荐：**
- Claude Desktop: 使用 `desktop-app`（默认）
- Claude Code: 使用 `claude-code`
- VSCode/JetBrains: 使用 `ide`
- Codex: 必须使用 `codex`

### 模式 (Modes)

动态切换以专注特定任务类型：

- **`planning`**: 规划模式 - 专注于分析和规划
- **`editing`**: 编辑模式 - 专注于代码修改
- **`one-shot`**: 一次性完成任务

**切换方法：** 使用 Serena MCP 提供的 `switch_mode` 工具动态切换

## 安全与成本

### 安全注意事项

- `execute_shell_command` 允许执行任意代码
- 使用时应检查执行参数
- 仅分析任务可在项目配置中设置 `read_only: true`

### 成本优化

**Token 节省：**
- 只检索必要的代码符号，而非全文扫描
- 通常能明显降低 Token 成本

**免费使用：**
- 通过 Claude Desktop 应用可在免费层级使用
- 避免 API 成本

## 激活与故障排除

### 命令行激活步骤

如果 MCP 工具不可用，可以通过命令行手动激活 Serena：

**1. 检查项目配置**
```bash
# 查看项目配置（应该已存在）
ls -la .serena/project.yml
```

**2. 添加项目到全局配置**

这是最关键的步骤！如果遇到 `'NoneType' object is not iterable` 错误，说明全局配置中的 `projects:` 列表为空。

```bash
# 编辑全局配置
vim ~/.serena/serena_config.yml

# 在 projects: 下添加项目路径
projects:
- /path/to/your/project
```

**3. 建立索引**
```bash
# 为项目建立索引（推荐，加速符号搜索）
uvx --from git+https://github.com/oraios/serena serena project index
```

### 验证 Serena 状态

**检查进程**：
```bash
ps aux | grep serena | grep -v grep
```

**访问 Web 仪表板**：
```
http://localhost:24282/dashboard/
```

**查看全局配置**：
```bash
cat ~/.serena/serena_config.yml | grep -A 5 "projects:"
```

### MCP 工具使用技巧

**1. 激活项目**

在使用任何 Serena 工具之前，必须先激活项目：

```python
# 使用 MCP 工具激活
mcp__serena__activate_project(project="project-name")
```

如果遇到 "No active project" 错误，说明需要先激活项目。

**2. 直接调用 MCP 工具**

即使 ToolSearch 找不到 serena 工具，也可以直接调用：

```python
# 直接调用工具（无需 ToolSearch）
mcp__serena__find_symbol(name_path_pattern="ClassName")
mcp__serena__list_dir(relative_path=".", recursive=False)
mcp__serena__get_symbols_overview(relative_path="path/to/file.py")
```

**3. 常用工具**

- `activate_project` - 激活项目（必须首先调用）
- `find_symbol` - 查找符号定义
- `find_referencing_symbols` - 查找符号引用
- `get_symbols_overview` - 获取文件符号概览
- `list_dir` - 列出目录内容
- `find_file` - 查找文件
- `read_file` - 读取文件内容
- `replace_symbol_body` - 替换符号主体

## 常见问题

### Q: Serena 不响应工具调用？

**A:** 可能原因：
1. 未激活项目 - 先调用 `mcp__serena__activate_project` 激活项目
2. FileSystemMCP 冲突 - 在 Claude Desktop 中禁用 FileSystemMCP
3. 项目未索引 - 对大型项目，运行 `serena project index` 建立索引
4. 全局配置问题 - 检查 `~/.serena/serena_config.yml` 中的 `projects:` 列表是否包含项目路径

### Q: 如何查看 Serena 的日志？

**A:** 访问 Web 仪表板：`http://localhost:24282/dashboard/index.html`

### Q: Codex 显示工具执行失败？

**A:** Codex 的已知 Bug，即使成功执行也可能显示 `failed`

## 详细配置与安装

完整的安装、配置和客户端集成指南，请参阅：

- **[完整参考文档](references/full-guide.md)** - 详细的安装、配置和使用教程
- **[客户端配置](references/client-config.md)** - 各客户端（Claude Desktop, Codex, Cursor 等）的配置方法
- **[工具参考](references/tools-reference.md)** - 所有可用工具的完整参考

## 快速参考

**核心用法示例：**
- "分析这个项目的架构，找出可以优化的地方"
- "帮我找出所有调用 UserService 的地方"
- "重构这个函数，提取公共逻辑并确保符合项目现有风格"
- "检查这段代码是否存在内存泄漏或潜在 Bug"
- "激活当前目录作为 Serena 项目"

**注意：** 所有 Serena MCP 工具由 Claude Code 自动调用，用户只需自然语言描述需求即可。
