---
name: skill-creator
description: 创建和维护符合 Codex CLI 规范的技能指南。用于新增或更新 `.codex/skills/<skill-name>/SKILL.md` 及配套 `assets/`、`references/`、`scripts/` 资源；当用户提到“创建 skill”“制作技能”“更新技能”“编写 SKILL.md”“优化技能触发条件”时使用。
---

# Skill Creator（Codex 规范版）

用于为 Codex 构建可复用、可触发、可执行的技能，并确保与本项目约束一致。

## Codex 兼容规则（必须）

1. Skill 主文件必须命名为 `SKILL.md`。
2. Frontmatter 仅保留 `name` 与 `description` 两个字段。
3. `description` 必须写明“做什么 + 何时用 + 触发词”。
4. 正文使用祈使句，直接描述执行动作，不写冗长背景。
5. 禁止引用不可用机制（如 `AskUserQuestion`、`CLAUDE.md`、`.claude/settings.local.json`）。
6. 禁止编造工具名，统一使用 Codex 可用能力（如 `update_plan`、`apply_patch`、`exec_command`）。
7. 仅按需创建 `assets/`、`references/`、`scripts/`，避免空目录和无效样例。
8. 创建 `scripts/` 时必须提供明确入口命令、输入参数与最小验证方式。

## 推荐目录结构

```text
.codex/skills/<skill-name>/
├── SKILL.md
├── assets/        # 可选：模板、样例输入、产出骨架
├── references/    # 可选：外部规范、术语表、校验标准
└── scripts/       # 可选：自动化生成/校验脚本
```

## 执行流程

### 1) 收集最小输入

至少确认以下信息：

- 技能名称（slug，建议小写+连字符）
- 目标问题（要解决什么重复任务）
- 触发场景（用户会如何描述需求）
- 产出物（要创建/更新哪些文件）
- 约束条件（权限、格式、风格、禁止事项）

如果信息不足，一次只补问 1-2 个关键问题。

### 2) 设计触发描述

优先把触发逻辑写进 `description`，正文只放执行流程。

推荐句式：

`<能力概述>。用于<任务范围/文件范围>；当用户提到"<关键词1>"、"<关键词2>"或需要<场景>时使用。`

### 3) 选择资源策略

- 只有固定模板重复出现时，才创建 `assets/`。
- 只有需要按需加载知识时，才创建 `references/`。
- 只有步骤容易出错且可自动化时，才创建 `scripts/`。

当创建 `scripts/` 时，必须同步定义：

- 脚本入口（如 `scripts/generate.sh` 或 `scripts/validate.py`）
- 调用命令（如 `bash scripts/generate.sh <arg>`）
- 输入/输出约定（读哪些文件、写哪些文件）
- 最小验证命令（至少能在当前项目跑通一次）

优先最小可用版本：先交付高质量 `SKILL.md`，再按需补资源。

### 4) 编写 `SKILL.md`

按以下结构组织：

1. 核心目标（1-2 句）
2. 必须遵守（硬规则）
3. 执行流程（分步）
4. 校验清单（可验证）
5. 失败回退（信息不足/执行受阻时）

可直接复用 `assets/skill-template.md`。

### 5) 最小验证

完成后至少检查：

- [ ] 文件名是 `SKILL.md`
- [ ] frontmatter 只有 `name` 和 `description`
- [ ] `description` 已包含触发场景与关键词
- [ ] 正文没有出现 Claude 专属机制或不可用工具
- [ ] 目录中没有无用途的空资源文件
- [ ] 若包含 `scripts/`，已给出可执行命令与参数说明
- [ ] 若包含 `scripts/`，已执行最小验证并记录结果

可参考 `references/codex-skill-checklist.md`。

## 输出格式建议

交付时给出：

1. 创建/修改的文件列表
2. 触发描述（最终版）
3. 验证结果（通过项/待补项）
4. 下一步建议（是否补 scripts 或示例）

## 失败回退策略

- 用户目标模糊：先产出最小版 `SKILL.md` 草案，再用 1 个问题确认方向。
- 约束冲突：优先遵循系统/项目规则，其次遵循技能内建议。
- 需要高风险操作：暂停并请求确认，不自行绕过权限。

## 参考文件

- `assets/skill-template.md`
- `references/codex-skill-checklist.md`
