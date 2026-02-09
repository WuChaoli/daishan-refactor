---
name: project-init
description: Initialize project for Codex CLI with docs structure, Codex workflow rules, and Serena activation
---

# Project Init (Codex)

自动初始化项目，面向 **Codex CLI** 工作流，完成以下配置：

1. **Codex 规则对齐** - 使用 AGENTS.md（注入 `.codex/company-rules/` 正文）+ 会话权限模型
2. **文档结构** - 创建上下文工程目录与索引
3. **工具激活** - 激活 Serena MCP（项目级）

## Usage

```bash
/init
```

或：

```bash
/project-init
```

## 执行步骤

### 1. Codex 规则对齐

请采用以下方式：

- **运行时权限**：由会话环境提供（如 `sandbox_mode`、`approval_policy`）
- **项目规则**：写入 `AGENTS.md`（行为规范、工具使用边界、工作流）
- **规则正文注入**：若存在 `.codex/company-rules/`，优先通过 `.codex/skills/project-init/scripts/inject-company-rules.sh` 注入 `AGENTS.md`
- **可见化文档**：创建 `docs/static/guide/codex-permissions.md`，记录当前项目建议权限策略

推荐在该文档中记录：

- 允许的常用只读命令（如 `ls`、`cat`、`rg`）
- 需要确认的操作（如跨目录写入、联网、潜在破坏性命令）
- 多步骤任务必须维护 `update_plan`
- 修改文件优先使用 `apply_patch`

推荐在 `AGENTS.md` 中加入以下“规则注入头部”（初始化时将 `.codex/company-rules/*.md` 正文拼接到该文件）：

```markdown
# Project Rules (Codex)

## 规则来源

- 本文件由 `project-init` 自动生成。
- 已按顺序注入以下规则正文：
  1. `.codex/company-rules/workflow.md`
  2. `.codex/company-rules/code-dev.md`
  3. `.codex/company-rules/code-quality.md`
  4. `.codex/company-rules/context-engineering.md`

## 执行基线

- 多步骤任务必须维护 `update_plan`
- 工具调用前必须先发送一句 preamble
- 修改文件优先使用 `apply_patch`
- 跨工作区写入、网络访问、潜在破坏性命令需先确认
```

### 2. 文档结构创建

创建上下文工程文档目录结构：

```
docs/
├── static/              # 静态文档
│   ├── architecture/    # 系统架构
│   ├── design/          # 模块设计
│   ├── api/             # 接口文档
│   ├── guide/           # 使用指南
│   └── spec/            # 需求规格
├── contexts/            # 开发上下文
│   └── .contexts-index.json
└── archive/             # 归档文档
```

同时创建 `docs/contexts/.contexts-index.json`：

```json
{
  "activeContexts": [],
  "archivedContexts": [],
  "lastUpdated": "2026-02-07T00:00:00Z"
}
```

### 3. Serena MCP 激活

Codex 下 Serena 通常通过全局配置启用（如 `~/.codex/config.toml`），项目初始化阶段应：

1. 检查 Serena MCP 工具是否可用
2. 激活项目：`mcp__serena__activate_project project="."`
3. 可选检查：`mcp__serena__check_onboarding_performed`

> 说明：`~/.codex/config.toml` 属于用户全局环境，`project-init` 不应在项目内强制改写它。

## 执行流程

```bash
# 步骤 1: 检查当前环境
pwd

# 步骤 2: 创建/更新 AGENTS.md（自动注入 .codex/company-rules/ 正文）
if [ -f .codex/skills/project-init/scripts/inject-company-rules.sh ]; then
  .codex/skills/project-init/scripts/inject-company-rules.sh AGENTS.md
else
  echo "[WARN] .codex/skills/project-init/scripts/inject-company-rules.sh 不存在，跳过规则注入"
fi

# 步骤 3: 创建文档目录结构
mkdir -p docs/static/{architecture,design,api,guide,spec}
mkdir -p docs/contexts
mkdir -p docs/archive

# 步骤 4: 创建上下文索引
cat > docs/contexts/.contexts-index.json << 'EOF'
{
  "activeContexts": [],
  "archivedContexts": [],
  "lastUpdated": "2026-02-07T00:00:00Z"
}
EOF

# 步骤 5: 创建 Codex 权限说明文档
cat > docs/static/guide/codex-permissions.md << 'EOF'
# Codex 权限与执行策略

## 会话权限模型

- 运行时权限由会话环境控制（sandbox + approval policy）
- 非工作区写入、联网、潜在破坏性操作需显式确认

## 建议允许操作

- 只读浏览：ls, cat, rg, find
- 项目内编辑：通过 apply_patch 修改受控文件

## 需确认操作

- 跨目录写入
- 网络访问
- 删除/重置类命令（如 rm、git reset）

## 工作流要求

- 多步骤任务使用 update_plan 跟踪状态
- 先说明下一步，再执行工具调用
EOF

# 步骤 6: 创建 docs 说明
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
- **archive/** - 归档文档（已完成需求）

## 相关命令

- `/context-engineering` - 上下文管理
- `/serena-mcp` - Serena MCP 工具
EOF

echo "✓ Codex 项目初始化文件已创建"
```

Serena 激活（通过 MCP 工具，不是 shell 命令）：

```text
mcp__serena__activate_project project="."
mcp__serena__check_onboarding_performed
```

## 输出示例

```markdown
✓ Codex 项目初始化完成

## Codex 规则
已采用会话权限模型（sandbox_mode + approval_policy）
已创建: AGENTS.md（已注入 rules 正文）
已执行: .codex/skills/project-init/scripts/inject-company-rules.sh AGENTS.md
已创建: docs/static/guide/codex-permissions.md

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
文档入口: docs/README.md

## Serena MCP
已执行: mcp__serena__activate_project project="."
可选检查: mcp__serena__check_onboarding_performed

## 下一步
- 使用 /context-engineering 开始新需求
- 使用 /serena-mcp 进行符号级代码分析
```

## 注意事项

1. **权限来源**：Codex 权限由运行会话控制，不由项目文件强制覆盖
2. **全局配置**：若需配置 MCP，请在 `~/.codex/config.toml` 手动维护
3. **项目规范**：项目内行为规则统一维护在 `AGENTS.md`
4. **规则注入**：若存在 `.codex/company-rules/`，初始化时应将规则正文注入 `AGENTS.md`

## 相关技能

- **context-engineering** - 上下文工程文档管理
- **serena-mcp** - Serena MCP 工具

## 常见问题

**Q: Codex 的权限在哪里控制？**
A: 在会话运行参数（sandbox/approval）与执行时审批流程中控制。

**Q: Serena 为什么不写项目内 `.mcp.json`？**
A: Codex 常用全局 MCP 配置（`~/.codex/config.toml`）；项目初始化只负责激活项目。

**Q: 如何让组织规则在初始化后自动生效？**
A: `project-init` 会执行 `.codex/skills/project-init/scripts/inject-company-rules.sh AGENTS.md`，将 `.codex/company-rules/*.md` 正文注入 `AGENTS.md` 并立即生效。

**Q: rules 更新后如何同步到 AGENTS.md？**
A: 重新执行 `.codex/skills/project-init/scripts/inject-company-rules.sh AGENTS.md` 即可，仅自动区块会被更新，不影响其他内容。

## Arguments

$ARGUMENTS: (无参数)

## Related Commands

- `/context-engineering` - 上下文工程管理
- `/serena-mcp` - Serena MCP 工具
- `/checkpoint` - 检查点管理
