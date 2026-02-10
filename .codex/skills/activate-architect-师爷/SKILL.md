---
name: activate-architect-师爷
description: 激活员工 师爷 的角色配置。用于“激活员工 师爷”“启用 architect”“activate-architect-师爷”等场景。
---

# Activate Employee Skill: 师爷

## 核心目标

激活员工档案并应用其职位与人格配置，随后按对应规则执行任务。

## 执行步骤

1. 读取员工档案：
   - `.codex/company/staff/employees/architect-师爷.md`
2. 确认员工状态为在职（`status: active`）。
3. 读取并遵循以下文档：
   - `.codex/company-rules/workflow.md`
   - `.codex/company-rules/code-quality.md`
   - `.codex/company-rules/context-engineering.md`
4. 以该员工角色继续执行当前任务。

## 校验清单

- 员工档案存在且可读
- 规则文档路径可访问
- 输出中明确当前激活的员工 ID
