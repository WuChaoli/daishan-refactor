---
name: comp-hire-employee
description: '一键创建职位模板 + 人格模板 + 员工档案 + activate 技能。用于"招聘员工""一键创建员工体系""hire employee"场景。'
---

# Hire Employee Skill

安全地创建员工体系：先确认参数、再创建模板、再生成档案、最后激活技能。

## 输入信息

### 必需参数
- `--name`：员工姓名（如：王麻子）
- `--position`：职位英文标识（如：test-engineer）
- `--position-cn`：职位中文名称（如：测试工程师）
- `--personality`：人格类型英文标识（如：analytical-type）
- `--personality-cn`：人格类型中文名称（如：分析型）

### 可选参数
- `--department`：所属部门（默认：技术部）
- `--gender`：性别（默认：男）
- `--hire-date`：入职日期（默认：当天，格式：YYYY-MM-DD）
- `--position-brief`：职位简介（默认：自动生成）
- `--personality-traits`：人格特征（默认：结构化思维,结果导向,协作透明,风险意识）
- `--mode`：创建模式（full/position/personality，默认：full）

## 执行步骤

### 1. 参数验证

检查必需参数是否完整：

```bash
# 检查姓名
if [[ -z "$NAME" ]]; then
  echo "错误：--name 参数必需"
  exit 1
fi

# 检查职位
if [[ -z "$POSITION" || -z "$POSITION_CN" ]]; then
  echo "错误：--position 和 --position-cn 参数必需"
  exit 1
fi

# 检查人格
if [[ -z "$PERSONALITY" || -z "$PERSONALITY_CN" ]]; then
  echo "错误：--personality 和 --personality-cn 参数必需"
  exit 1
fi
```

### 2. 检查员工是否已存在

查询注册表，避免重复创建：

```bash
EMPLOYEE_ID="${POSITION}-${NAME}"
REGISTRY_FILE=".codex/company/staff/employees/.employees-registry.json"

if [[ -f "$REGISTRY_FILE" ]]; then
  EXISTING=$(jq -r --arg id "$EMPLOYEE_ID" '.employees[] | select(.employee_id==$id) | .employee_id' "$REGISTRY_FILE")
  if [[ -n "$EXISTING" ]]; then
    echo "警告：员工 $EMPLOYEE_ID 已存在"
    echo "是否覆盖？(y/N)"
    read -r CONFIRM
    if [[ "$CONFIRM" != "y" ]]; then
      exit 0
    fi
  fi
fi
```

### 3. 执行一键创建脚本

使用 `bootstrap_employee.sh` 完成全链路创建：

```bash
bash .codex/company/tools/bootstrap_employee.sh \
  --name "$NAME" \
  --position "$POSITION" \
  --position-cn "$POSITION_CN" \
  --department "$DEPARTMENT" \
  --personality "$PERSONALITY" \
  --personality-cn "$PERSONALITY_CN" \
  --gender "$GENDER" \
  --hire-date "$HIRE_DATE" \
  ${POSITION_BRIEF:+--position-brief "$POSITION_BRIEF"} \
  ${PERSONALITY_TRAITS:+--personality-traits "$PERSONALITY_TRAITS"}
```

### 4. 验证创建结果

检查所有产物是否正确生成：

```bash
EMPLOYEE_ID="${POSITION}-${NAME}"
COMMAND="activate-${EMPLOYEE_ID}"

# 检查职位模板
POSITION_FILE=".codex/company/catalog/positions/${POSITION}.md"
if [[ -f "$POSITION_FILE" ]]; then
  echo "✓ 职位模板已创建: $POSITION_FILE"
else
  echo "✗ 职位模板创建失败"
fi

# 检查人格模板
PERSONALITY_FILE=".codex/company/catalog/personalities/${PERSONALITY}.md"
if [[ -f "$PERSONALITY_FILE" ]]; then
  echo "✓ 人格模板已创建: $PERSONALITY_FILE"
else
  echo "✗ 人格模板创建失败"
fi

# 检查员工档案
EMPLOYEE_FILE=".codex/company/staff/employees/${EMPLOYEE_ID}.md"
if [[ -f "$EMPLOYEE_FILE" ]]; then
  echo "✓ 员工档案已创建: $EMPLOYEE_FILE"
else
  echo "✗ 员工档案创建失败"
fi

# 检查激活技能
SKILL_FILE=".codex/skills/${COMMAND}/SKILL.md"
if [[ -f "$SKILL_FILE" ]]; then
  echo "✓ 激活技能已创建: $SKILL_FILE"
else
  echo "✗ 激活技能创建失败"
fi

# 检查软链接
SYMLINK=".codex/skills/${COMMAND}/employee.md"
if [[ -L "$SYMLINK" ]]; then
  echo "✓ 软链接已创建: $SYMLINK"
else
  echo "✗ 软链接创建失败"
fi

# 检查注册表
REGISTRY_ENTRY=$(jq -r --arg id "$EMPLOYEE_ID" '.employees[] | select(.employee_id==$id)' "$REGISTRY_FILE")
if [[ -n "$REGISTRY_ENTRY" ]]; then
  echo "✓ 注册表已更新"
  echo "$REGISTRY_ENTRY" | jq '.'
else
  echo "✗ 注册表更新失败"
fi
```

### 5. 激活员工（可选）

创建完成后，可以立即激活员工：

```bash
# 使用 Claude Code 技能系统激活
echo "员工创建完成，可使用以下命令激活："
echo "  /${COMMAND}"
```

## 分步创建模式

### 仅创建职位模板

```bash
bash .codex/company/tools/bootstrap_employee.sh \
  --mode position \
  --position test-engineer \
  --position-cn 测试工程师 \
  --department 技术部 \
  --position-brief "负责测试方案设计与质量保障"
```

### 仅创建人格模板

```bash
bash .codex/company/tools/bootstrap_employee.sh \
  --mode personality \
  --personality analytical-type \
  --personality-cn 分析型 \
  --personality-traits "结构化思维,结果导向,协作透明,风险意识"
```

### 完整创建（默认）

```bash
bash .codex/company/tools/bootstrap_employee.sh \
  --mode full \
  --name 王麻子 \
  --position test-engineer \
  --position-cn 测试工程师 \
  --personality analytical-type \
  --personality-cn 分析型
```

## 目录结构

创建完成后的目录结构：

```text
.codex/
├── company/
│   ├── catalog/
│   │   ├── positions/
│   │   │   └── <position>.md          # 职位模板
│   │   └── personalities/
│   │       └── <personality>.md       # 人格模板
│   ├── staff/
│   │   └── employees/
│   │       ├── .employees-registry.json  # 员工注册表
│   │       └── <position>-<name>.md      # 员工档案
│   └── tools/
│       └── bootstrap_employee.sh      # 创建脚本
└── skills/
    └── activate-<position>-<name>/
        ├── SKILL.md                   # 激活技能
        └── employee.md                # 软链接 → 员工档案
```

## 安全约束

- 创建前必须验证所有必需参数
- 员工已存在时，必须确认是否覆盖
- 创建失败时，必须回滚已创建的文件
- 注册表更新失败时，必须报错并停止

## 输出格式

- 员工ID：`<position>-<name>`
- 激活命令：`activate-<position>-<name>`
- 创建结果：职位模板、人格模板、员工档案、激活技能、注册表
- 验证清单：所有产物的创建状态

## 常见问题

### Q: 如何修改已创建的员工信息？
A: 直接编辑员工档案文件 `.codex/company/staff/employees/<position>-<name>.md`，并同步更新注册表。

### Q: 如何删除员工？
A: 使用 `comp-fire-employee` 技能，或手动删除相关文件并更新注册表。

### Q: 职位模板和人格模板可以复用吗？
A: 可以。使用 `--mode full` 时，如果模板已存在，会直接复用，不会覆盖。

### Q: 如何查看所有员工？
A: 查询注册表：`jq '.employees[]' .codex/company/staff/employees/.employees-registry.json`
