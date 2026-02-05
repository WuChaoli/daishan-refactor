---
name: fire-employee
description: 删除员工档案和对应的激活命令。当用户提到"解雇员工"、"删除员工"、"fire employee"、"移除员工档案"或需要删除 company/employee/ 中的员工档案以及 commands/ 中对应的激活命令时使用。
---

# 员工解雇器

## 概述

删除员工档案和对应的激活命令，清理相关资源。

## 工作流程

### 1. 确认员工信息

**识别方式**（提供任一即可）：
- 员工ID（如：E2026020201）
- 员工姓名（如：张三）
- 命令文件名（如：load-test-engineer-zhang-san）

### 2. 查找员工档案

**优先方法：从配置文件查询**
```bash
# 按员工ID查询
cat company/employee/.employees-registry.json | jq '.employees[] | select(.employee_id=="E2026020201")'

# 按姓名查询
cat company/employee/.employees-registry.json | jq '.employees[] | select(.name=="张三")'

# 查询所有在职员工
cat company/employee/.employees-registry.json | jq '.employees[] | select(.status=="active")'
```

**备用方法：直接查找文件**
```bash
# 按ID查找
ls company/employee/[员工ID].md

# 按姓名查找
grep -l "name: [姓名]" company/employee/*.md
```

### 3. 确认要删除的文件

**必需删除**：
1. 员工档案：`company/employee/[员工ID].md`
2. 激活命令：`commands/load-[职位]-[姓名].md`

**确认步骤**：
```
即将删除以下文件：
- 员工档案：company/employee/E2026020201.md
- 激活命令：commands/load-test-engineer-zhang-san.md

确认删除？(是/否)
```

### 4. 更新员工配置文件

**配置文件位置**：`company/employee/.employees-registry.json`

**方式1：删除员工记录（不推荐）**
```bash
# 使用 jq 删除指定员工
jq 'del(.employees[] | select(.employee_id=="E2026020201"))' company/employee/.employees-registry.json > temp.json && mv temp.json company/employee/.employees-registry.json
```

**方式2：更新员工状态为 inactive（推荐）**
```bash
# 使用 jq 更新员工状态
jq '(.employees[] | select(.employee_id=="E2026020201") | .status) = "inactive" | .last_updated = "2026-02-04"' company/employee/.employees-registry.json > temp.json && mv temp.json company/employee/.employees-registry.json
```

**推荐做法**：保留员工记录，仅更新状态
- 将 `status` 更新为 `"inactive"`
- 添加 `termination_date` 字段记录离职日期
- 保留历史记录便于审计和查询

**完整更新示例**：
```bash
# 读取配置文件
CONFIG=$(cat company/employee/.employees-registry.json)

# 更新员工状态和离职日期
echo "$CONFIG" | jq --arg id "E2026020201" --arg date "2026-02-04" '
  (.employees[] | select(.employee_id==$id)) |= (
    .status = "inactive" |
    .termination_date = $date
  ) |
  .last_updated = $date
' > company/employee/.employees-registry.json
```

### 5. 执行删除

使用 Bash 工具删除文件：
```bash
rm company/employee/[员工ID].md
rm commands/load-[职位]-[姓名].md
```

### 6. 验证删除

```bash
# 确认档案已删除
ls company/employee/[员工ID].md 2>/dev/null || echo "员工档案已删除"

# 确认命令已删除
ls commands/load-[职位]-[姓名].md 2>/dev/null || echo "激活命令已删除"
```

## 快速开始

**第1步**：调用 `/fire-employee`

**第2步**：提供员工信息
```
员工ID: E2026020201
或
员工姓名: 张三
```

**第3步**：确认删除

**第4步**：完成

## 示例

### 示例1：按员工ID删除（使用配置文件）

**输入**：
```
员工ID: E2026020201
```

**执行步骤**：

1. **从配置文件查询员工信息**：
```bash
cat company/employee/.employees-registry.json | jq '.employees[] | select(.employee_id=="E2026020201")'
```

输出：
```json
{
  "employee_id": "E2026020201",
  "name": "张三",
  "position": "test-engineer",
  "personality": "analytical-type",
  "hire_date": "2026-02-02",
  "status": "active",
  "command": "load:test-engineer-张三",
  "file": "company/employee/E2026020201.md"
}
```

2. **确认删除**：
```
即将删除：
- 员工档案：company/employee/E2026020201.md
- 激活命令：commands/load-test-engineer-张三.md
- 配置记录：更新状态为 inactive

确认删除？是
```

3. **更新配置文件**：
```bash
jq --arg id "E2026020201" --arg date "2026-02-04" '
  (.employees[] | select(.employee_id==$id)) |= (
    .status = "inactive" |
    .termination_date = $date
  ) |
  .last_updated = $date
' company/employee/.employees-registry.json > temp.json && mv temp.json company/employee/.employees-registry.json
```

4. **删除文件**：
```bash
rm company/employee/E2026020201.md
rm commands/load-test-engineer-张三.md
```

**输出**：
```
✓ 配置文件已更新（员工状态：inactive）
✓ 员工档案已删除
✓ 激活命令已删除
```

### 示例2：按员工姓名删除（使用配置文件）

**输入**：
```
员工姓名: 张三
```

**执行步骤**：

1. **从配置文件查询员工信息**：
```bash
cat company/employee/.employees-registry.json | jq '.employees[] | select(.name=="张三")'
```

2. **提取关键信息**：
```bash
EMPLOYEE_INFO=$(cat company/employee/.employees-registry.json | jq -r '.employees[] | select(.name=="张三") | "\(.employee_id)|\(.file)|\(.command)"')
EMPLOYEE_ID=$(echo "$EMPLOYEE_INFO" | cut -d'|' -f1)
FILE_PATH=$(echo "$EMPLOYEE_INFO" | cut -d'|' -f2)
COMMAND=$(echo "$EMPLOYEE_INFO" | cut -d'|' -f3)
```

3. **确认并执行删除**：
```bash
# 更新配置文件
jq --arg name "张三" --arg date "2026-02-04" '
  (.employees[] | select(.name==$name)) |= (
    .status = "inactive" |
    .termination_date = $date
  ) |
  .last_updated = $date
' company/employee/.employees-registry.json > temp.json && mv temp.json company/employee/.employees-registry.json

# 删除文件
rm "$FILE_PATH"
rm "commands/load-test-engineer-张三.md"
```

**输出**：
```
✓ 配置文件已更新（员工状态：inactive）
✓ 员工档案已删除
✓ 激活命令已删除
```

## 注意事项

### 安全确认
- 删除前必须确认文件路径
- 显示即将删除的文件列表
- 等待用户确认后再执行

### 命令文件匹配
激活命令命名格式：`load-[职位]-[姓名].md`

如果命令文件名不是标准格式，可能需要手动查找：
```bash
# 查找包含该员工姓名的所有命令
ls commands/ | grep "load.*[姓名关键词]"
```

### 归档考虑
如需保留员工记录，建议先归档而非删除：
```bash
# 创建归档目录
mkdir -p company/employee/archived/

# 移动而非删除
mv company/employee/[员工ID].md company/employee/archived/
mv commands/load-[职位]-[姓名].md commands/archived/
```

## 错误处理

### 档案不存在
```
错误：找不到员工档案 [员工ID].md
请检查员工ID是否正确
```

### 命令文件不存在
```
警告：员工档案已删除，但激活命令文件不存在：
commands/load-[职位]-[姓名].md

可能原因：
- 命令文件已被手动删除
- 命令文件命名不符合规范
```

### 多个同名员工
```
警告：找到多个名为 [姓名] 的员工：
- E2026020201.md (测试工程师)
- E2026020205.md (产品经理)

请使用员工ID进行删除
```

## 相关资源

- **招聘员工**: `/hire-employee`
- **员工档案位置**: `company/employee/`
- **命令文件位置**: `commands/`

---

**版本**: 1.0.0 | **更新**: 2026-02-02
