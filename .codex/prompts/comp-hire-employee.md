---
name: comp-hire-employee
description: 从职位模板创建员工档案、更新员工注册表，并在 prompts 中创建指向员工档案的激活软链接。用于“招聘员工”“创建员工档案”“hire employee”等场景。
---

# Hire Employee Prompt

从 `.codex/company/position/` 的职位模板实例化员工，并在 `.codex/prompts/` 生成可用的 `load-*` 激活软链接（指向员工档案）。

## 输入信息

必需：
- 员工姓名（如：王麻子）
- 职位英文名（如：test-engineer）
- 人格英文名（如：analytical-type）

可选：
- 性别（默认：男）
- 入职日期（默认：当天，格式 `YYYY-MM-DD`）

## 执行步骤

1. 校验基础资源是否存在
   - `.codex/company/position/<position>.md`
   - `.codex/company/personality/<personality>.md`

2. 生成标识
   - `employee_id = <position>-<name>`
   - 激活软链接：`.codex/prompts/load-<position>-<name>.md`
   - 命令名：`load:<position>-<name>`

3. 创建员工档案
   - 路径：`.codex/company/employee/<position>-<name>.md`
   - 使用以下模板：

```markdown
---
employee_id: <position>-<name>
name: <name>
gender: <gender>
position: <position>
personality: <personality>
hire_date: <YYYY-MM-DD>
status: active
---

# <name> - <职位中文名>

## 基本信息
- **ID**: <position>-<name>
- **姓名**: <name>
- **性别**: <gender>
- **职位**: <职位中文名> ([<position>](.codex/company/position/<position>.md))
- **人格**: <人格中文名> ([<personality>](.codex/company/personality/<personality>.md))
- **入职日期**: <YYYY-MM-DD>
- **状态**: 在职

## 职位与人格
- **职位模板**: [.codex/company/position/<position>.md](.codex/company/position/<position>.md)
- **人格模板**: [.codex/company/personality/<personality>.md](.codex/company/personality/<personality>.md)
```

4. 更新员工注册表
   - 文件：`.codex/company/employee/.employees-registry.json`
   - 若不存在则创建：

```json
{
  "version": "1.0.0",
  "last_updated": "<YYYY-MM-DD>",
  "employees": []
}
```

   - 追加记录：

```json
{
  "employee_id": "<position>-<name>",
  "name": "<name>",
  "position": "<position>",
  "personality": "<personality>",
  "hire_date": "<YYYY-MM-DD>",
  "status": "active",
  "command": "load:<position>-<name>",
  "file": ".codex/company/employee/<position>-<name>.md"
}
```

5. 创建激活软链接（不再创建独立 prompt 文件）
   - 链接路径：`.codex/prompts/load-<position>-<name>.md`
   - 目标路径：`.codex/company/employee/<position>-<name>.md`
   - 建议命令：

```bash
LINK_PATH=".codex/prompts/load-<position>-<name>.md"
TARGET_PATH="../company/employee/<position>-<name>.md"

# 若已存在旧文件或旧链接，先删除再创建
[ -e "$LINK_PATH" ] || [ -L "$LINK_PATH" ] && rm "$LINK_PATH"

ln -s "$TARGET_PATH" "$LINK_PATH"
```

6. 输出结果
   - 新建文件与软链接列表
   - 注册表更新结果
   - 激活命令（如：`/load-test-engineer-王麻子`）

## 校验清单

- 员工档案路径存在且 frontmatter 完整
- 注册表 `employees` 中新增记录且 `last_updated` 已更新
- `.codex/prompts/load-<position>-<name>.md` 为软链接（`test -L`）
- 软链接目标正确指向 `../company/employee/<position>-<name>.md`（`readlink` 校验）
