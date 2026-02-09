# Codex Skill Checklist

用于在交付前快速检查技能是否符合 Codex 项目规范。

## 文件结构

- [ ] 位于 `.codex/skills/<skill-name>/SKILL.md`
- [ ] 主文件名严格为 `SKILL.md`
- [ ] 仅在需要时才包含 `assets/`、`references/`、`scripts/`
- [ ] 若包含 `scripts/`，脚本文件命名清晰且入口可识别

## Frontmatter

- [ ] 包含 `name`
- [ ] 包含 `description`
- [ ] 不包含额外字段（如 `tools`、`model`、`permissionMode`）

## 触发设计

- [ ] `description` 说明“做什么”
- [ ] `description` 说明“何时用”
- [ ] `description` 包含 2-5 个高相关触发词

## 正文质量

- [ ] 以执行流程为主，避免冗长背景
- [ ] 包含“必须遵守”约束
- [ ] 包含“校验清单”
- [ ] 包含“失败回退策略”
- [ ] 若包含 `scripts/`，包含调用命令、参数与 I/O 说明

## Codex 兼容性

- [ ] 不出现 Claude 专属机制（如 `AskUserQuestion`、`CLAUDE.md`）
- [ ] 工具名与当前环境一致（如 `update_plan`、`apply_patch`、`exec_command`）
- [ ] 涉及高风险操作时要求用户确认

## 最小验收

- [ ] 用户可据此技能独立创建或更新目标文件
- [ ] 交付输出包含：文件清单、触发描述、验证结果、下一步建议
- [ ] 若包含 `scripts/`，至少有 1 条已执行的最小验证记录
