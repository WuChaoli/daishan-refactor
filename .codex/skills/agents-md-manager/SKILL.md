---
name: agents-md-manager
description: 动态维护 AGENTS.md 的治理区块与结构快照。用于“同步 AGENTS 规则”“校验 AGENTS 动态区块”“查看 AGENTS 差异”“初始化 AGENTS 动态 marker”等场景。仅维护 AGENTS.md 本体，不修改 CLAUDE.md、activate-*、project-init 等外部文件。
---

# AGENTS MD Manager

## Overview

执行 `AGENTS.md` 的动态治理维护：初始化动态区块、同步区块内容、校验区块完整性、输出可审计差异。

## Hard Constraints

- 仅修改 `AGENTS.md`。
- 仅允许改写 marker 包裹的动态区块：
  - `<!-- BEGIN AGENTS-DYNAMIC:<BLOCK_ID> -->`
  - `<!-- END AGENTS-DYNAMIC:<BLOCK_ID> -->`
- 不自动修改 `CLAUDE.md`、`.codex/skills/activate-*`、`.codex/skills/project-init`。

## Commands

执行脚本：`.codex/skills/agents-md-manager/scripts/agents_md_manager.py`

- 初始化动态区块：
  - `python .codex/skills/agents-md-manager/scripts/agents_md_manager.py init-blocks --agents AGENTS.md`
- 同步动态区块：
  - `python .codex/skills/agents-md-manager/scripts/agents_md_manager.py sync --agents AGENTS.md --root .`
- 校验动态区块：
  - `python .codex/skills/agents-md-manager/scripts/agents_md_manager.py check --agents AGENTS.md --root .`
- 预览差异：
  - `python .codex/skills/agents-md-manager/scripts/agents_md_manager.py diff --agents AGENTS.md --root .`

## Workflow

1. 先执行 `init-blocks`（首次接入或 marker 缺失时）。
2. 执行 `sync` 写入结构快照与 8 个治理区块。
3. 执行 `check` 作为提交前门禁。
4. 执行 `diff` 产出审计信息（区块名 + 摘要行数）。

## Failure Handling

- `check` 返回 `1`：存在 marker 异常、缺失区块或结构统计过期，必须先修复再提交。
- `sync` 返回 `1` 且提示缺失区块：先运行 `init-blocks`。
- 返回 `2`：命令参数或路径错误，先修复输入路径。

## References

- 动态区块字段规范：`references/agents_schema.md`
- marker 协议与错误码：`references/marker_contract.md`
