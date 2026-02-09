---
name: comp-fire-employee
description: 删除员工档案与激活软链接，并更新员工注册表状态。用于“解雇员工”“删除员工”“fire employee”等场景。
---

# Fire Employee Prompt

安全地下线员工：先确认、再更新注册表、再删除文件。

## 输入信息

提供以下任一项：
- `employee_id`（优先）
- 员工姓名
- 激活命令文件名

## 执行步骤

1. 查找员工记录（优先查注册表）

```bash
cat .codex/company/employee/.employees-registry.json | jq '.employees[]'
```

按 ID 查询：

```bash
cat .codex/company/employee/.employees-registry.json | jq '.employees[] | select(.employee_id=="<employee_id>")'
```

按姓名查询：

```bash
cat .codex/company/employee/.employees-registry.json | jq '.employees[] | select(.name=="<name>")'
```

2. 解析目标文件
- 员工档案：`.codex/company/employee/<position>-<name>.md`（或注册表中的 `file`）
- 激活软链接：`.codex/prompts/load-<position>-<name>.md`

3. 删除前确认（必须）
- 列出将删除的路径
- 等待用户明确确认

4. 更新注册表（推荐保留历史）
- 文件：`.codex/company/employee/.employees-registry.json`
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
' .codex/company/employee/.employees-registry.json > /tmp/employees.json && mv /tmp/employees.json .codex/company/employee/.employees-registry.json
```

5. 删除文件/软链接

```bash
rm .codex/company/employee/<position>-<name>.md

# 优先按软链接处理；若历史遗留为普通文件也一并删除
if [ -L .codex/prompts/load-<position>-<name>.md ]; then
  rm .codex/prompts/load-<position>-<name>.md
elif [ -f .codex/prompts/load-<position>-<name>.md ]; then
  rm .codex/prompts/load-<position>-<name>.md
fi
```

6. 验证结果

```bash
ls .codex/company/employee/<position>-<name>.md 2>/dev/null || echo "员工档案已删除"
ls .codex/prompts/load-<position>-<name>.md 2>/dev/null || echo "激活命令已删除"

# 删除前可选校验（推荐）：确认其为软链接并查看指向
test -L .codex/prompts/load-<position>-<name>.md && readlink .codex/prompts/load-<position>-<name>.md
```

## 安全约束

- 未确认前，不执行删除
- 优先“状态下线”而非直接删除注册表记录
- 若目标不存在，返回可操作错误（不静默失败）

## 输出格式

- 目标员工：`<employee_id> / <name>`
- 注册表更新：成功/失败
- 删除结果：员工档案、激活软链接
- 后续建议：是否需要归档离职员工资料
