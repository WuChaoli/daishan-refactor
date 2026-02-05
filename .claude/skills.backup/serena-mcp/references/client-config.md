# 客户端配置参考

本指南详细介绍如何在各种客户端中配置和使用 Serena MCP。

---

## 目录

1. [Claude Desktop](#1-claude-desktop-windowsmacos)
2. [Claude Code (CLI)](#2-claude-code-cli)
3. [VSCode](#3-vscode)
4. [Codex (OpenAI CLI)](#4-codex-openai-cli)
5. [JetBrains IDEs](#5-jetbrains-ides)
6. [Antigravity](#6-antigravity)
7. [其他 MCP 客户端](#7-其他-mcp-客户端)
8. [WSL2 集成](#8-wsl2-集成)

---

## 1. Claude Desktop (Windows/macOS)

### 为什么选择 Claude Desktop？

- **免费使用**: 在 Claude 的免费层级上即可工作
- **无 API 成本**: 避免使用付费 API
- **最佳体验**: 官方支持，稳定性高

### 配置步骤

#### 1.1 打开配置文件

1. 打开 Claude Desktop 应用
2. 进入菜单：`File` → `Settings` → `Developer` → `MCP Servers` → `Edit Config`
3. 这将打开 `claude_desktop_config.json` 配置文件

#### 1.2 添加 Serena 配置

**使用 uvx（推荐）:**

```json
{
  "mcpServers": {
    "serena": {
      "command": "/absolute/path/to/uvx",
      "args": [
        "--from",
        "git+https://github.com/oraios/serena",
        "serena",
        "start-mcp-server"
      ]
    }
  }
}
```

**关键要点：**
- `command` 必须是 uvx 的**绝对路径**
- 在 macOS/Linux 上通常在 `/Users/username/.local/bin/uvx`
- 在 Windows 上通常在 `C:\Users\username\.local\bin\uvx.exe`

#### 1.3 重启应用

**重要**: 保存配置后，必须：
1. 完全退出 Claude Desktop 应用（Cmd+Q 或 Ctrl+Q）
2. 重新启动应用

仅关闭窗口不会重启 MCP 服务器！

#### 1.4 指定项目（可选）

如果希望 Serena 自动连接到特定项目，可以在 `args` 中添加 `--project` 参数：

```json
{
  "mcpServers": {
    "serena": {
      "command": "/absolute/path/to/uvx",
      "args": [
        "--from",
        "git+https://github.com/oraios/serena",
        "serena",
        "start-mcp-server",
        "--project",
        "/path/to/your/project"
      ]
    }
  }
}
```

#### 1.5 使用不同上下文

如果需要使用特定的上下文（如 `ide-assistant`）：

```json
{
  "mcpServers": {
    "serena": {
      "command": "/absolute/path/to/uvx",
      "args": [
        "--from",
        "git+https://github.com/oraios/serena",
        "serena",
        "start-mcp-server",
        "--context",
        "ide-assistant"
      ]
    }
  }
}
```

### 故障排除

#### 问题：Claude 注册了 Serena 但不调用其工具

**解决方案**: 禁用 FileSystemMCP

在 `claude_desktop_config.json` 中注释掉或删除 FileSystemMCP 配置：

```json
{
  "mcpServers": {
    // "filesystem": {
    //   "command": "npx",
    //   "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"]
    // },
    "serena": {
      "command": "/absolute/path/to/uvx",
      "args": ["--from", "git+https://github.com/oraios/serena", "serena", "start-mcp-server"]
    }
  }
}
```

**原因**: FileSystemMCP 和 Serena 可能存在工具名称冲突。

---

## 2. Claude Code (CLI)

### 快速配置（项目级别）

在项目目录下运行：

```bash
claude mcp add serena -- \
  uvx --from git+https://github.com/oraios/serena \
  serena start-mcp-server \
  --context claude-code \
  --project $(pwd)
```

**配置说明：**
- **`--context claude-code`**: Claude Code 专用上下文，禁用重复工具
- **`--project $(pwd)`**: 自动使用当前目录作为项目

### 全局配置（跨项目）

使用 `--project-from-cwd` 进行用户级别配置，适用于所有项目：

```bash
claude mcp add --scope user serena -- \
  uvx --from git+https://github.com/oraios/serena \
  serena start-mcp-server \
  --context claude-code \
  --project-from-cwd
```

**工作原理：**
- 启动时自动从当前目录向上查找 `.serena/project.yml` 或 `.git` 标记
- 如果未找到标记，自动激活当前目录作为项目
- 适合单一全局 MCP 配置

### 验证配置

检查 `.claude/mcp.json` 文件：

```json
{
  "mcpServers": {
    "serena": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/oraios/serena",
        "serena",
        "start-mcp-server",
        "--context",
        "claude-code",
        "--project",
        "/current/working/directory"
      ]
    }
  }
}
```

### Token 效率优化

**启用按需工具加载**（Claude Code v2.0.74+ 支持）：

设置环境变量 `ENABLE_TOOL_SEARCH=true`，避免启动时加载所有工具描述，节省 Token。

**临时启用（单次会话）：**
```bash
# bash/zsh
ENABLE_TOOL_SEARCH=true claude

# Windows CMD
set ENABLE_TOOL_SEARCH=true && claude
```

**永久启用：** 在系统环境变量中设置 `ENABLE_TOOL_SEARCH=true`

---

## 3. VSCode

### 手动配置（推荐）

虽然可以直接从 GitHub MCP 服务器注册表安装，但建议手动配置（直到注册表配置改进）。

将以下内容粘贴到 `/.vscode/mcp.json`，或在使用"安装到工作区"后编辑：

```json
{
  "servers": {
    "oraios/serena": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/oraios/serena",
        "serena",
        "start-mcp-server",
        "--context",
        "ide",
        "--project",
        "${workspaceFolder}"
      ]
    }
  },
  "inputs": []
}
```

**配置说明：**
- **`--context ide`**: IDE 上下文，减少工具重复
- **`--project ${workspaceFolder}`**: 使用当前工作区作为项目

---

## 4. Codex (OpenAI CLI)

### 配置要求

Codex 并非完全支持 MCP 规范，需要使用特定的上下文：`--context codex`

### 配置步骤

1. 编辑全局配置文件 `~/.codex/config.toml`（如果文件不存在则创建）

2. 添加以下配置：

```toml
[mcp_servers.serena]
command = "uvx"
args = [
  "--from",
  "git+https://github.com/oraios/serena",
  "serena",
  "start-mcp-server",
  "--context",
  "codex"
]
```

3. 保存配置

### 激活项目

由于 Codex 是全局配置，每次对话开始时需要激活项目：

> "Activate the current directory as project using serena"

### 已知问题

**问题**: Codex 经常显示工具执行 `failed`，即使它们已成功执行

**说明**: 这是 Codex 的一个已知 Bug，不影响实际功能

**查看日志**: 检查 `~/.codex/log/codex-tui.log`

**Dashboard 访问**: `http://localhost:24282/dashboard/index.html`

---

## 5. JetBrains IDEs

### JetBrains Junie（全局配置）

1. 打开 Junie
2. 点击右上角三点菜单 → Settings → MCP Settings
3. 添加 Serena 到全局 MCP 服务器配置：

```json
{
  "mcpServers": {
    "serena": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/oraios/serena",
        "serena",
        "start-mcp-server",
        "--context",
        "ide"
      ]
    }
  }
}
```

**激活项目**: 每次会话开始时提示 Junie"使用 serena 的激活工具激活当前项目"

### JetBrains AI Assistant（项目配置）

AI Assistant 支持更方便的每项目 MCP 服务器配置，可以指定启动工作目录。

1. 进入 Settings → Tools → AI Assistant → MCP
2. 通过 `as JSON` 选项添加新的 **本地** 配置：

```json
{
  "mcpServers": {
    "serena": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/oraios/serena",
        "serena",
        "start-mcp-server",
        "--context",
        "ide",
        "--project",
        "$(pwd)"
      ]
    }
  }
}
```

3. **重要**: 配置工作目录为项目根目录

---

## 6. Antigravity

### 配置步骤

添加以下配置：

```json
{
  "mcpServers": {
    "serena": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/oraios/serena",
        "serena",
        "start-mcp-server",
        "--context",
        "ide"
      ]
    }
  }
}
```

**激活项目**: 在项目目录启动 Antigravity 后，提示代理"使用 serena 的激活工具激活当前项目"

**注意事项：**
- 只需在第一个聊天中激活一次，后续会话将继续使用同一 Serena 会话
- 与 VSCode 不同，Antigravity 目前不支持在 MCP 配置中包含工作目录
- 当前客户端在 Serena 的仪表板中显示为 `none`（Antigravity 不完全支持 MCP 规范），不影响功能

---

## 7. 其他 MCP 客户端

### 终端类客户端

支持 MCP 的终端编码助手，通常受益于 Serena 提供的符号工具：

- **Gemini-CLI**
- **Qwen3-Coder**
- **rovodev**
- **OpenHands CLI**
- **opencode**

**推荐配置**: 使用 `--context ide` 减少工具重复

可能需要编写自定义上下文、模式或提示词以调整到客户端的内部能力和工作流程。

### MCP 支持的 IDE 和编码客户端

大多数流行的编码助手（IDE 扩展）和 AI IDE 支持 MCP 连接：

- **Cline**
- **Roo-Code**
- **Cursor**
- **Windsurf**

**推荐**: 使用 `--context ide` 以减少工具重复

### 本地 GUI 和代理框架

允许运行本地 GUI 客户端并连接到 MCP 服务器：

- **Jan**
- **OpenHands**
- **OpenWebUI**
- **Agno**

这些应用允许将 Serena 与几乎任何 LLM（包括本地运行的）结合使用。

### 通用配置建议

大多数 MCP 客户端使用类似的配置格式：

```json
{
  "mcpServers": {
    "serena": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/oraios/serena",
        "serena",
        "start-mcp-server",
        "--context",
        "ide",
        "--project",
        "/path/to/project"
      ]
    }
  }
}
```

**推荐使用 `--context ide`** 参数以获得最佳的 IDE 集成体验。

### 成本注意事项

通过这些客户端使用 Serena 时：
- 仍需支付所选 LLM 的 **API 费用**
- 不会像 Claude Desktop 那样免费使用

---

## 8. WSL2 集成

### 使用场景

在 Windows 上运行 Claude Desktop，但希望 Serena 安装在 **WSL2** (Ubuntu) 中。

### 配置方法

在 `claude_desktop_config.json` 中，使用 `wsl.exe` 前缀：

```json
{
  "mcpServers": {
    "serena": {
      "command": "wsl.exe",
      "args": [
        "-d",
        "Ubuntu",
        "uvx",
        "--from",
        "git+https://github.com/oraios/serena",
        "serena",
        "start-mcp-server"
      ]
    }
  }
}
```

### 指定项目路径

在 WSL2 中，Windows 路径需要转换为 `/mnt/` 格式：

```json
{
  "mcpServers": {
    "serena": {
      "command": "wsl.exe",
      "args": [
        "-d",
        "Ubuntu",
        "uvx",
        "--from",
        "git+https://github.com/oraios/serena",
        "serena",
        "start-mcp-server",
        "--project",
        "/mnt/c/path/to/project"
      ]
    }
  }
}
```

### 其他 WSL2 发行版

如果使用的是其他 WSL2 发行版（如 Debian），将 `Ubuntu` 替换为相应的发行版名称：

```json
{
  "mcpServers": {
    "serena": {
      "command": "wsl.exe",
      "args": [
        "-d",
        "Debian",
        "uvx",
        "--from",
        "git+https://github.com/oraios/serena",
        "serena",
        "start-mcp-server"
      ]
    }
  }
}
```

---

## 9. 上下文和模式详解

### 上下文 (Contexts)

上下文在启动时设置，定义操作环境：

| 上下文 | 说明 | 使用场景 |
|--------|------|----------|
| `desktop-app` | 默认上下文 | Claude Desktop 应用 |
| `agent` | 更自主的代理模式 | 需要高度自主性的任务 |
| `ide` | IDE 集成模式 | VSCode、JetBrains 等 IDE |
| `claude-code` | Claude Code CLI 专用 | Claude Code 命令行工具 |
| `codex` | Codex 专用上下文 | OpenAI Codex CLI |

**推荐**:
- Claude Desktop: 使用 `desktop-app`（默认）
- Claude Code: 使用 `claude-code`
- VSCode/JetBrains: 使用 `ide`
- Codex: 必须使用 `codex`

### 模式 (Modes)

模式可以动态切换，专注于特定任务类型：

| 模式 | 说明 | 使用场景 |
|------|------|----------|
| `planning` | 规划模式 | 分析和规划任务 |
| `editing` | 编辑模式 | 代码修改和重构 |
| `one-shot` | 一次性完成 | 简单任务，快速完成 |

**切换方法**: 使用 `switch_modes` 工具

---

## 10. 配置示例总结

### Claude Desktop（推荐）

```json
{
  "mcpServers": {
    "serena": {
      "command": "/Users/yourname/.local/bin/uvx",
      "args": [
        "--from",
        "git+https://github.com/oraios/serena",
        "serena",
        "start-mcp-server"
      ]
    }
  }
}
```

### Claude Code CLI

**项目级别：**
```bash
claude mcp add serena -- \
  uvx --from git+https://github.com/oraios/serena \
  serena start-mcp-server \
  --context claude-code \
  --project $(pwd)
```

**全局级别：**
```bash
claude mcp add --scope user serena -- \
  uvx --from git+https://github.com/oraios/serena \
  serena start-mcp-server \
  --context claude-code \
  --project-from-cwd
```

### Codex

```toml
[mcp_servers.serena]
command = "uvx"
args = [
  "--from",
  "git+https://github.com/oraios/serena",
  "serena",
  "start-mcp-server",
  "--context",
  "codex"
]
```

### WSL2 (Windows)

```json
{
  "mcpServers": {
    "serena": {
      "command": "wsl.exe",
      "args": [
        "-d",
        "Ubuntu",
        "uvx",
        "--from",
        "git+https://github.com/oraios/serena",
        "serena",
        "start-mcp-server"
      ]
    }
  }
}
```

---

## 11. 项目配置

### 只读模式

如果只进行分析而不修改代码，可以在项目配置中设置 `read_only: true`。

在项目根目录创建 `.serena/config.json`：

```json
{
  "read_only": true
}
```

这将禁用所有修改操作，提供额外的安全保障。

---

## 12. 验证配置

### 检查 MCP 服务器状态

1. 打开客户端应用
2. 查看开发者工具或日志
3. 确认 Serena 已成功注册

### 测试 Serena

在对话中输入：

> "激活当前目录作为项目"

如果成功，Serena 应该：
1. 执行入职流程
2. 创建 `.serena/memories/` 目录
3. 开始响应工具调用

---

## 13. 常见问题与故障排除

### 常见陷阱

#### 正确转义路径

如果客户端配置使用 JSON，特殊字符（如反斜杠）需要正确转义。特别是在 Windows 上指定包含反斜杠的路径时，确保正确转义（`\\\\`）。或者直接使用正斜杠。

#### uvx 可发现性

客户端可能找不到 `uvx` 命令，即使它在系统 PATH 中。解决方法是提供 `uvx` 可执行文件的完整路径。

#### 环境变量

某些语言服务器可能需要设置额外的环境变量（如 macOS 上 Homebrew 的 F#），可能需要在 MCP 服务器配置中显式添加。

对于某些客户端（如 Claude Desktop），生成的 MCP 服务器进程可能不会继承仅在 shell 配置文件中配置的环境变量（如 `.bashrc`、`.zshrc` 等）；需要设置为系统级环境变量。

简单的解决方法是在 MCP 服务器条目中显式添加它们。例如，在 Claude Desktop 和其他客户端中，可以简单地添加 `env` 键：

```json
"env": {
  "DOTNET_ROOT": "/opt/homebrew/Cellar/dotnet/9.0.8/libexec"
}
```

### 获取帮助

如果遇到问题：

1. **查看日志**: 访问 `http://localhost:24282/dashboard/index.html`
2. **检查配置**: 确保路径和参数正确
3. **重启应用**: 完全退出并重启客户端
4. **查看文档**: 访问 [GitHub 仓库](https://github.com/oraios/serena)
