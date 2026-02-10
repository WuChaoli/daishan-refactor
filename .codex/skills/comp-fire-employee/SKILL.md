---
name: comp-fire-employee
description: "下线员工并更新注册表状态，同时移除对应的 activate 技能。用于“解雇员工”“删除员工”“fire employee”等场景。"
---

# Fire Employee Skill

安全地下线员工：先确认、再更新注册表、再删除文件。

## 输入信息

提供以下任一项：
- `employee_id`（优先）
- 员工姓名
- 激活命令文件名（`activate-*`）

## 执行步骤

1. 查找员工记录（优先查注册表）

```bash
cat .codex/company/staff/employees/.employees-registry.json | jq '.employees[]'
```

按 ID 查询：

```bash
cat .codex/company/staff/employees/.employees-registry.json | jq '.employees[] | select(.employee_id=="<employee_id>")'
```

按姓名查询：

```bash
cat .codex/company/staff/employees/.employees-registry.json | jq '.employees[] | select(.name=="<name>")'
```

2. 解析目标文件
- 员工档案：`.codex/company/staff/employees/<position>-<name>.md`（或注册表中的 `file`）
- 激活技能目录：`.codex/skills/<command>`（`command` 来自注册表）

3. 删除前确认（必须）
- 列出将删除的路径
- 等待用户明确确认

4. 更新注册表（推荐保留历史）
- 文件：`.codex/company/staff/employees/.employees-registry.json`
- 将目标员工更新为：
  - `status: "inactive"`
  - `termination_date: "<YYYY-MM-DD>"`
- 更新 `last_updated`

示例：

```bash
jq --arg id "<employee_id>" --arg date "<YYYY-MM-DD>" '
  (.employees[] | select(.employee_id==$id)) |= (
    .status = "inactive" |
    .termination_date = $date
  ) |
  .last_updated = $date
' .codex/company/staff/employees/.employees-registry.json > /tmp/employees.json && mv /tmp/employees.json .codex/company/staff/employees/.employees-registry.json
```

5. 删除员工档案与激活技能

```bash
EMPLOYEE_ID="<employee_id>"
REGISTRY_FILE=".codex/company/staff/employees/.employees-registry.json"

COMMAND_NAME="$(jq -r --arg id "$EMPLOYEE_ID" '.employees[] | select(.employee_id==$id) | .command // empty' "$REGISTRY_FILE")"
EMPLOYEE_FILE="$(jq -r --arg id "$EMPLOYEE_ID" '.employees[] | select(.employee_id==$id) | .file // empty' "$REGISTRY_FILE")"

[ -n "$EMPLOYEE_FILE" ] || EMPLOYEE_FILE=".codex/company/staff/employees/<position>-<name>.md"
[ -n "$COMMAND_NAME" ] || COMMAND_NAME="activate-<position>-<name>"

SKILL_DIR=".codex/skills/$COMMAND_NAME"

rm -f "$EMPLOYEE_FILE"
rm -rf "$SKILL_DIR"
rm -f ".codex/prompts/$COMMAND_NAME.md"
```

6. 验证结果

```bash
ls "$EMPLOYEE_FILE" 2>/dev/null || echo "员工档案已删除"
ls "$SKILL_DIR/SKILL.md" 2>/dev/null || echo "激活技能已删除"
ls ".codex/prompts/$COMMAND_NAME.md" 2>/dev/null || echo "命令 prompt 入口已删除"
```

## 安全约束

- 未确认前，不执行删除
- 优先“状态下线”而非直接删除注册表记录
- 若目标不存在，返回可操作错误（不静默失败）

## 输出格式

- 目标员工：`<employee_id> / <name>`
- 注册表更新：成功/失败
- 删除结果：员工档案、激活技能目录、prompt 入口
- 后续建议：是否需要归档离职员工资料
