# Serena MCP 完整参考文档

本指南提供 Serena MCP 的完整安装、配置和使用教程。

---

## 一、环境准备与服务器启动

### 1. 前提条件：安装 `uv`

Serena 的命令行操作由 `uv` 驱动，需要先安装它。

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux / macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**验证安装：**
```bash
uv --version
```

### 2. 启动 Serena MCP 服务器

Serena 必须作为 MCP 服务器运行。通常，客户端（如 Claude Desktop）会将其作为子进程启动，通过标准输入输出（stdio）进行通信。

#### 使用 `uvx` 快速启动（推荐）

`uvx` 可以直接从仓库运行最新版本的 Serena，无需本地克隆：

```bash
uvx --from git+https://github.com/oraios/serena serena start-mcp-server
```

#### 本地安装与运行

1. 克隆仓库：
```bash
git clone https://github.com/oraios/serena && cd serena
```

2. 运行服务器：
```bash
uv run serena start-mcp-server
```

3. 如果从 `serena` 安装目录之外运行，必须指定目录：
```bash
uv run --directory /abs/path/to/serena serena start-mcp-server
```

4. 如果需要全局安装，完成以上步骤后可直接在任意项目中启动。

#### 使用 Docker (实验性)

Docker 提供了更好的安全隔离和一致的环境，无需本地安装语言服务器：

```bash
docker run --rm -i --network host \
  -v /path/to/your/projects:/workspaces/projects \
  ghcr.io/oraios/serena:latest \
  serena start-mcp-server --transport stdio
```

### 3. 仪表板和日志

默认情况下，Serena 会启动一个 Web 仪表板：
- **地址**: `http://localhost:24282/dashboard/index.html`
- **功能**: 显示日志和允许用户关闭 MCP 服务器（防止客户端关闭时遗留僵尸进程）

---

## 二、客户端配置

Serena 可以与任何支持 Model Context Protocol (MCP) 的客户端集成。

### 1. Claude Desktop (Windows/macOS)

这是**免费使用** Serena 功能的最佳途径，因为它在 Claude 的免费层级上即可工作。

**配置步骤：**

1. 打开 Claude Desktop，进入 `File / Settings / Developer / MCP Servers / Edit Config`
2. 这将打开 `claude_desktop_config.json` 文件
3. 在 `mcpServers` 部分添加 Serena 配置

**使用 `uvx` 的配置示例：**

```json
{
  "mcpServers": {
    "serena": {
      "command": "/abs/path/to/uvx",
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

**重要提示：**
- `command` 必须是 uvx 的**绝对路径**
- 保存配置后，**必须完全退出 Claude Desktop 应用程序并重启**

**故障排除：**
如果 Claude 注册了 Serena 但不调用其工具，建议**禁用 FileSystemMCP**，因为它可能存在工具名称冲突。

#### Windows WSL2 集成

如果在 Windows 上运行 Claude Desktop，但 Serena 安装在 **WSL2** (Ubuntu) 中，需要通过 `wsl.exe` 来调用服务器：

在 `claude_desktop_config.json` 中，命令应以 `wsl.exe -d Ubuntu` 为前缀：

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

### 2. Codex (OpenAI CLI)

Codex 并非完全支持 MCP 规范，因此需要使用特定的上下文。

**配置步骤：**

1. 在全局配置文件 `~/.codex/config.toml` 中添加配置（如果文件不存在则创建）：

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

**重要提示：** 必须使用 `--context codex` 参数。

2. **启动后激活项目：** 由于 Codex 是全局配置，必须通过提示 LLM 来激活项目，否则 Serena 的工具将无法使用：

   > "Activate the current dir as project using serena"

3. **日志和故障排除：** Codex 经常会显示工具执行 `failed`，即使它们已成功执行，这似乎是 Codex 的一个 Bug。

### 3. Claude Code (CLI)

在项目目录下，使用 `claude mcp add` 命令添加 Serena。推荐使用 `ide-assistant` 上下文。

```bash
claude mcp add serena -- \
  uvx --from git+https://github.com/oraios/serena \
  serena start-mcp-server \
  --context ide-assistant \
  --project $(pwd)
```

### 4. 其他 MCP 客户端 (Cursor, Cline, Roo-Code, Windsurf)

Serena 作为 MCP 服务器，可以被任何支持 MCP 的客户端集成，包括 IDE 扩展或类 VSCode 的 IDE。

**配置建议：** 强烈建议在 `args` 中使用 **`--context ide-assistant`**。

**成本注意：** 通过这些客户端使用 Serena，仍需支付所选 LLM 的 **API 费用**。

### 5. 本地 GUI 和其他 LLM (Agno, OpenWebUI)

Serena 不限于 Claude。通过 Agno、OpenWebUI 或 Jan 等本地 GUI 工具，可以将 Serena 与 **Gemini** 或 **本地部署的模型**（如 Ollama/LM Studio）结合使用。

- 使用 Agno 或其他非 Claude 客户端通常需要 **API Key**，因此会产生费用。

---

## 三、实际使用和操作流程

Serena 旨在提供 IDE 级别的工具，如符号搜索 (`find_symbol`) 和符号后插入 (`insert_after_symbol`)，而不是依赖于文件读取或文本搜索。

### 1. 项目激活与索引

在使用 Serena 的工具之前，必须先让 LLM 知道它正在处理哪个项目。

**激活项目：** 通过提示 LLM 激活项目路径：

> "激活项目 /path/to/my_project"

**项目索引：** 对于大型项目，为了**加速 Serena 的工具运行**，建议先对项目进行索引：

```bash
uvx --from git+https://github.com/oraios/serena serena project index
```

**单项目限制：** Serena 当前只能处理**一个项目文件** (`one project file at once`)。

### 2. 首次启动：项目入职（Onboarding）与记忆

Serena 具有独特的记忆系统。

**入职流程：** 首次在项目上启动 Serena 时，它会执行 **onboarding 过程**：
- 分析项目结构
- 识别关键信息
- 提取重要业务逻辑

这些信息存储在 `.serena/memories/` 目录下的**记忆文件**中。

**记忆利用：** 在后续对话中，LLM 可以选择性地读取这些记忆文件，从而更好地理解用户需求。

**绕过入职：** 如果 LLM 未完成入职流程或想跳过，可以在 `.serena/memories/` 中创建一个文件，Serena 就不会再次触发入职。

### 3. 编码、编辑与自主代理行为

Serena 提供的工具能够支持复杂的编码工作流。

**符号级编辑：** 主要编辑操作是 **`replace_symbol_body`**（替换符号的完整主体），它比基于文本的替换更准确。

**自主纠错（Agent Loop）：** 建议启用 `execute_shell_command` 工具（在 Claude Desktop 中默认启用），这样 Serena 可以：
- 执行代码
- 运行测试
- 自主识别并纠正错误

**安全注意：** `execute_shell_command` 允许执行任意代码。使用时应检查执行参数。如果只进行分析而不修改代码，可在项目配置文件中设置 `read_only: true`。

**节省 Token：** Serena 只检索必要的代码符号而非全文扫描，通常能明显降低 Token 成本。

### 4. 避免上下文超限

对于长而复杂的任务，或当 LLM 上下文接近限制时，最好在新对话中继续。

**`prepare_for_new_conversation`：** Serena 有一个专用工具可以**创建当前状态的摘要**并保存为记忆。在新对话中要求 Serena 读取该记忆，从而无缝地继续未完成的任务。

### 5. 模式和上下文定制

可以使用 **上下文（Contexts）** 和 **模式（Modes）** 来调整 Serena 的行为和工具集。

#### 上下文 (Contexts)

在启动时设置，定义操作环境：

- **`desktop-app`**（默认）: Claude Desktop 应用环境
- **`agent`**: 更自主的代理模式
- **`ide-assistant`**: 集成到 IDE 中

#### 模式 (Modes)

可以动态切换，用于专注于特定任务类型：

- **`planning`**（规划）: 专注于分析和规划
- **`editing`**（编辑）: 专注于代码修改
- **`one-shot`**: 一次性完成任务

使用 `switch_modes` 工具来动态切换模式。

---

## 四、常见问题

### Q: Serena 注册成功但不响应工具调用？

**A:** 可能原因：
1. 未激活项目 - 先运行"激活项目 /path/to/project"
2. FileSystemMCP 冲突 - 在 Claude Desktop 中禁用 FileSystemMCP
3. 项目未索引 - 对大型项目运行 `serena project index`

### Q: 如何查看 Serena 的日志？

**A:** 访问 Web 仪表板：`http://localhost:24282/dashboard/index.html`

### Q: Codex 显示工具执行失败？

**A:** Codex 的已知 Bug，即使成功执行也可能显示 `failed`

---

## 五、资源链接

- **GitHub 仓库**: https://github.com/oraios/serena
- **官方文档**: [查看仓库中的 README 和文档]
