---
name: employee-orchestrator
description: 智能编排员工激活与角色执行。默认每个 session 仅在首次或手动切换时进行一次路由；后续回合直接沿用当前已激活员工，仅依赖会话上下文状态。
---

# Employee Orchestrator

## Rule

由 Codex 当前 AI 直接判断应激活员工

会话级约束：
- 默认每个 session 只编排一次。
- 编排状态仅依赖当前会话上下文（不落盘，不写状态文件）。
- 仅当用户手动指定切换员工时，才重新路由/激活。

## Workflow

1. 读取用户请求与约束。
2. 检查会话上下文是否已有 `active_employee` 与 `active_command`。
3. 若用户明确指定 `activate-*`（或明确点名切换到某员工），执行重新激活。
4. 若会话内尚未激活员工，则读取在职员工注册表：`.codex/company/staff/employees/.employees-registry.json`，并按路由规则选择最匹配员工；若信息不充分，可进行一次或多次澄清后再选。
5. 若会话内已激活且用户未手动切换：跳过路由，直接沿用当前员工执行任务。
6. 在发生激活/切换时，加载：
   - `.codex/skills/<command>/SKILL.md`
   - `.codex/skills/<command>/employee.md`
7. 激活后需继续执行当前用户任务，不得只输出路由结果后停住。

## Routing

- `architect`：架构设计、技术选型、系统边界、方案评审
- `requirement-planner`：需求澄清、任务拆解、验收标准
- `refactor-engineer`：重构、技术债、结构优化
- `tdd-developer`：TDD、先写测试、红绿重构
- `test-engineer`：测试设计、回归验证、覆盖率
- `archive-assistant`：文档归档、上下文迁移、索引更新

Tie-break：
1. 显式 `activate-*` 优先。
2. “TDD + 重构”优先 `tdd-developer`。
3. “归档/索引更新”优先 `archive-assistant`。
4. “架构设计/技术方案”优先 `architect`。
5. 仍冲突则先澄清。

## Output Contract

仅在「首次激活 / 手动切换」时进行简略路由输出：
- `selected_employee`（仅输出激活员工）

非路由回合（沿用已激活员工）不重复输出路由信息。
完成简略路由输出后，必须立即继续执行用户任务，不得停在路由结果。

## Mimic Protocol

激活后首条响应仅声明当前员工，并继续处理用户当前请求；
后续计划/验证/交付格式保持与该员工一致，未经用户允许不得混用其他员工规则。
