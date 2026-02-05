---
description: Initialize project with optimized permissions, context structure, and tooling
---

# Project Init

自动初始化项目，完成以下配置：

1. **权限配置** - 优化文件读写权限
2. **文档结构** - 创建上下文工程文档目录
3. **工具激活** - 加载 Serena MCP

## Usage

```bash
/project-init
```

## 执行步骤

### 1. 权限配置

自动更新 `.claude/settings.local.json`，添加以下权限规则：

**自动允许**：
- 编辑和写入文档文件：`*.md`, `*.txt`
- 编辑 `docs/` 和 `doc/` 目录
- 读取项目内所有文件：`Read(./**/*)`, `Read($PROJECT_PATH/**/*)`
- 在项目内搜索：`Grep`, `Glob`（支持 path 和 pattern 参数）
- 常用 Bash 命令：`grep`, `cat`, `ls`, `find`, `head`, `tail`, `tree`
- MCP 工具：Serena（代码分析）、Chrome DevTools（浏览器）、GitHub（代码仓库）、Context7（文档查询）

**需要询问**：
- 配置文件编辑：`*.json`, `*.yaml`, `*.yml`
- 读取其他项目的 .md 文件：`/Users/wuchaoli/codespace/**/*.md`
- 读取 home 目录的 .md 文件：`~/**/*.md`
- 在项目外执行命令

### 2. 文档结构创建

创建上下文工程文档目录结构：

```
docs/
├── static/           # 静态文档
│   ├── architecture/  # 系统架构
│   ├── design/       # 模块设计
│   ├── api/          # 接口文档
│   ├── guide/        # 使用指南
│   └── spec/         # 需求规格
├── contexts/         # 开发上下文
│   └── .contexts-index.json
└── archive/          # 归档文档
```

同时创建 `docs/contexts/.contexts-index.json` 索引文件：

```json
{
  "activeContexts": [],
  "archivedContexts": [],
  "lastUpdated": "2026-02-04T13:00:00Z"
}
```

### 3. Serena MCP 激活

自动激活 Serena MCP 项目级工具：

- 检查 `.claude/.mcp.json` 是否存在
- 添加或确认 `serena` 配置
- 激活项目：`mcp__serena__activate_project project="."`

## 执行流程

```bash
# 步骤 1: 检查当前环境
pwd

# 步骤 2: 创建/更新权限配置
PROJECT_PATH=$(pwd)
cat > .claude/settings.local.json << EOF
{
  "permissions": {
    "allow": [
      "Bash(tree *)",
      "Bash(grep *)",
      "Bash(cat *)",
      "Bash(ls *)",
      "Bash(find *)",
      "Bash(head *)",
      "Bash(tail *)",
      "Read(./**/*)",
      "Read($PROJECT_PATH/**/*)",
      "Grep(path=./**/*)",
      "Grep(path=$PROJECT_PATH/**/*)",
      "Glob(pattern=./**/*)",
      "Glob(pattern=$PROJECT_PATH/**/*)",
      "Glob(path=./**/*)",
      "Glob(path=$PROJECT_PATH/**/*)",
      "Edit(**/*.md)",
      "Write(**/*.md)",
      "Edit(**/*.txt)",
      "Write(**/*.txt)",
      "Edit(**/docs/**/*)",
      "Write(**/docs/**/*)",
      "Edit(**/doc/**/*)",
      "Write(**/doc/**/*)",
      "mcp__chrome-devtools__list_pages",
      "mcp__chrome-devtools__take_snapshot",
      "mcp__chrome-devtools__navigate_page",
      "mcp__chrome-devtools__take_screenshot",
      "mcp__chrome-devtools__evaluate_script",
      "mcp__serena__read_file",
      "mcp__serena__list_dir",
      "mcp__serena__find_file",
      "mcp__serena__search_for_pattern",
      "mcp__serena__get_symbols_overview",
      "mcp__serena__find_symbol",
      "mcp__serena__find_referencing_symbols",
      "mcp__serena__read_memory",
      "mcp__serena__list_memories",
      "mcp__serena__get_current_config",
      "mcp__plugin_serena_serena__read_file",
      "mcp__plugin_serena_serena__list_dir",
      "mcp__plugin_serena_serena__find_file",
      "mcp__plugin_serena_serena__search_for_pattern",
      "mcp__plugin_serena_serena__get_symbols_overview",
      "mcp__plugin_serena_serena__find_symbol",
      "mcp__plugin_serena_serena__find_referencing_symbols",
      "mcp__plugin_serena_serena__read_memory",
      "mcp__plugin_serena_serena__list_memories",
      "mcp__plugin_serena_serena__get_current_config",
      "mcp__github__get_file_contents",
      "mcp__github__search_code",
      "mcp__github__search_repositories",
      "mcp__github__list_commits",
      "mcp__github__list_issues",
      "mcp__github__get_issue",
      "mcp__github__get_pull_request",
      "mcp__github__list_pull_requests",
      "mcp__github__get_pull_request_files",
      "mcp__github__get_pull_request_status",
      "mcp__github__get_pull_request_comments",
      "mcp__github__get_pull_request_reviews",
      "mcp__plugin_context7_context7__query-docs",
      "mcp__plugin_context7_context7__resolve-library-id"
    ]
  },
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": [
    "serena"
  ]
}
EOF

# 步骤 3: 创建文档目录结构
mkdir -p docs/static/{architecture,design,api,guide,spec}
mkdir -p docs/contexts
mkdir -p docs/archive

# 步骤 4: 创建上下文索引

cat > docs/contexts/.contexts-index.json << 'EOF'
{
  "activeContexts": [],
  "archivedContexts": [],
  "lastUpdated": "2026-02-04T13:00:00Z"
}
EOF

# 步骤 5: 配置 Serena MCP
if [ ! -f .claude/.mcp.json ]; then
  cat > .claude/.mcp.json << 'EOF'
{
  "mcpServers": {
    "serena": {
      "command": "npx",
      "args": ["-y", "serena-mcp"]
    }
  }
}
EOF
fi

# 步骤 6: 创建 README
cat > docs/README.md << 'EOF'
# 项目文档

本文档遵循上下文工程规范组织开发工作。

## 目录结构

- **static/** - 静态文档（长期维护）
  - architecture/ - 系统架构
  - design/ - 模块设计
  - api/ - 接口文档
  - guide/ - 使用指南
  - spec/ - 需求规格

- **contexts/** - 开发上下文（按时间+功能组织）
  - 使用 `/context-engineering` 技能管理

- **archive/** - 归档文档（已完成需求）

## 工作流程

1. 开始新需求：使用 context-manager agent
2.开始新需求：[功能名称]
3. 查看活跃上下文：查看活跃上下文
4. 归档已完成：归档 [contextId]

## 相关命令

- `/context-engineering` - 上下文管理
- `/serena-mcp` - Serena MCP 工具
EOF

echo "✓ 项目初始化完成"
```

## 输出示例

```markdown
✓ 项目初始化完成

## 权限配置
已更新: .claude/settings.local.json

自动允许:
- 文档编辑：*.md, *.txt
- 项目内读取：./**/*, $PROJECT_PATH/**
- 搜索工具：Grep, Glob（支持 path 和 pattern 参数）
- Bash 命令：grep, cat, ls, find, head, tail, tree
- MCP 工具：
  - Chrome DevTools（5个工具）
  - Serena（18个工具）
  - GitHub（12个工具）
  - Context7（2个工具）

询问确认:
- 配置文件编辑：*.json, *.yaml, *.yml
- 其他项目的 .md 文件：/Users/wuchaoli/codespace/**/*.md
- Home 目录的 .md 文件：~/**/*.md
- 项目外执行命令

## 文档结构
已创建:
- docs/static/architecture/
- docs/static/design/
- docs/static/api/
- docs/static/guide/
- docs/static/spec/
- docs/contexts/
- docs/archive/

索引文件: docs/contexts/.contexts-index.json

## Serena MCP
已配置: .claude/.mcp.json
已激活: serena

## 静态文档
已创建: docs/README.md

## 下一步
- 使用 /context-engineering 开始新需求
- 使用 /serena-mcp 访问符号级代码工具
```

## 注意事项

1. **权限配置**: 修改在下次会话启动时生效
2. **文档结构**: 遵循上下文工程规范
3. **Serena MCP**: 提供 LSP 符号级代码理解能力
4. **上下文管理**: 使用专门的 agent 管理开发上下文
5. **MCP 工具通配符**: `mcp__*` 通配符不被支持，需要列出具体工具
6. **配置文件安全**: .json/.yaml 文件不自动允许编辑，需要询问确认

## 相关技能

- **context-engineering** - 上下文工程文档管理
- **serena-mcp** - Serena MCP 工具

## 常见问题

**Q: 权限配置没有立即生效？**
A: 权限配置在下次 Claude Code 会话启动时生效。

**Q: 如何使用上下文管理？**
A: 使用 `/context-engineering` 技能或 context-manager agent。

**Q: Serena MCP 有什么用？**
A: 提供 LSP 符号级代码导航、搜索、重构等高级功能。

**Q: 文档放在哪里？**
A:
- 静态文档放在 `docs/static/`（长期维护）
- 开发上下文放在 `docs/contexts/`（动态开发）
- 已归档文档放在 `docs/archive/`（只读）

## Arguments

$ARGUMENTS: (无参数)

## Related Commands

- `/context-engineering` - 上下文工程管理
- `/serena-mcp` - Serena MCP 工具
- `/checkpoint` - 检查点管理
