#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

MODE="full"
NAME=""
POSITION=""
POSITION_CN=""
DEPARTMENT="技术部"
PERSONALITY=""
PERSONALITY_CN=""
GENDER="男"
HIRE_DATE="$(date +%F)"
POSITION_BRIEF=""
PERSONALITY_TRAITS=""

usage() {
  cat <<USAGE
Usage:
  bash .codex/company/tools/bootstrap_employee.sh \\
    [--mode full|position|personality] \\
    [--name <姓名>] \\
    [--position <position-en>] \\
    [--position-cn <职位中文名>] \\
    [--department <部门>] \\
    [--personality <personality-en>] \\
    [--personality-cn <人格中文名>] \\
    [--gender <男|女>] \\
    [--hire-date <YYYY-MM-DD>] \\
    [--position-brief <简介>] \\
    [--personality-traits <特征逗号分隔>]

Modes:
  full         创建职位 + 人格 + 员工 + activate 技能（默认）
  position     仅创建/更新职位模板
  personality  仅创建/更新人格模板
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode) MODE="$2"; shift 2 ;;
    --name) NAME="$2"; shift 2 ;;
    --position) POSITION="$2"; shift 2 ;;
    --position-cn) POSITION_CN="$2"; shift 2 ;;
    --department) DEPARTMENT="$2"; shift 2 ;;
    --personality) PERSONALITY="$2"; shift 2 ;;
    --personality-cn) PERSONALITY_CN="$2"; shift 2 ;;
    --gender) GENDER="$2"; shift 2 ;;
    --hire-date) HIRE_DATE="$2"; shift 2 ;;
    --position-brief) POSITION_BRIEF="$2"; shift 2 ;;
    --personality-traits) PERSONALITY_TRAITS="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1"; usage; exit 1 ;;
  esac
done

if [[ -z "$PERSONALITY_TRAITS" ]]; then
  PERSONALITY_TRAITS="结构化思维,结果导向,协作透明,风险意识"
fi

if [[ "$MODE" == "full" || "$MODE" == "position" ]]; then
  if [[ -z "$POSITION" ]]; then
    echo "--position is required in mode=$MODE"
    exit 1
  fi
  if [[ -z "$POSITION_CN" ]]; then
    POSITION_CN="$POSITION"
  fi
  if [[ -z "$POSITION_BRIEF" ]]; then
    POSITION_BRIEF="负责${POSITION_CN}相关方案设计、实施推进与质量保障，确保交付可追踪、可维护、可演进。"
  fi
fi

if [[ "$MODE" == "full" || "$MODE" == "personality" ]]; then
  if [[ -z "$PERSONALITY" ]]; then
    echo "--personality is required in mode=$MODE"
    exit 1
  fi
  if [[ -z "$PERSONALITY_CN" ]]; then
    PERSONALITY_CN="$PERSONALITY"
  fi
fi

if [[ "$MODE" == "full" ]]; then
  if [[ -z "$NAME" ]]; then
    echo "--name is required in mode=full"
    exit 1
  fi
fi

prepare_layout() {
  mkdir -p .codex/company/catalog/positions
  mkdir -p .codex/company/catalog/personalities
  mkdir -p .codex/company/staff/employees
  mkdir -p .codex/company/tools
}

extract_body() {
  awk 'BEGIN{c=0} /^---[[:space:]]*$/{c++; next} c>=2 {print}' "$1"
}

create_position() {
  local position_file=".codex/company/catalog/positions/${POSITION}.md"
  cat > "$position_file" <<POS
---
role: ${POSITION}
position: ${POSITION_CN}
department: ${DEPARTMENT}
version: 1.0.0
created: ${HIRE_DATE}
updated: ${HIRE_DATE}
skills:
  fixed:
    - doc-location-manager
  role_specific:
    - tdd-workflow
    - requesting-code-review
agents:
  recommended:
    - name: serena-mcp
      purpose: 代码符号级分析与定位
---

# ${POSITION_CN} 职位模板

## 概述
${POSITION_BRIEF}

## 核心职责
- 负责与该岗位相关的需求拆解、技术方案与落地实现。
- 管理交付节奏，确保关键路径可验证、可回滚。
- 维护质量门槛，保证异常路径和边界输入被覆盖。
- 对跨模块协作输出明确接口、依赖与验收标准。
- 对结果进行复盘沉淀，持续优化流程与规范。

## 次要职责
- 维护岗位知识库与模板资产。
- 支持关键问题排查与根因定位。
- 参与代码审查并推动问题闭环。

## 必需规则
- workflow.md
- code-quality.md
- context-engineering.md

## 文档产出
- docs/contexts/<context-id>/requirement.md
- docs/contexts/<context-id>/design.md
- docs/contexts/<context-id>/task-todo.md

## 质量检查
- [ ] 输入信息完整且可执行
- [ ] 核心流程有验证证据
- [ ] 异常路径有处理策略
- [ ] 文档与实现保持一致
POS
}

create_personality() {
  local personality_file=".codex/company/catalog/personalities/${PERSONALITY}.md"
  cat > "$personality_file" <<PER
---
personality: ${PERSONALITY}
name: ${PERSONALITY_CN}
category: 通用型
stage: 执行
---

# ${PERSONALITY_CN}

## 核心特征
${PERSONALITY_TRAITS}

## 工作风格
- 沟通：先结论后细节，明确边界与依赖。
- 决策：优先验证假设，避免并发猜测性改动。
- 协作：小步快跑，持续同步状态与风险。
- 节奏：每轮改动都附带最小可证明验证。

## 适配建议
- 适用于需稳定交付与流程治理的岗位。
- 适合作为跨团队协作中的默认人格模板。
PER
}

create_employee_and_skill() {
  local employee_id="${POSITION}-${NAME}"
  local command="activate-${employee_id}"
  local employee_file=".codex/company/staff/employees/${employee_id}.md"
  local skill_dir=".codex/skills/${command}"
  local skill_file="${skill_dir}/SKILL.md"
  local registry_file=".codex/company/staff/employees/.employees-registry.json"

  local position_body personality_body
  position_body="$(extract_body ".codex/company/catalog/positions/${POSITION}.md")"
  personality_body="$(extract_body ".codex/company/catalog/personalities/${PERSONALITY}.md")"

  cat > "$employee_file" <<EMP
---
employee_id: ${employee_id}
name: ${NAME}
gender: ${GENDER}
position: ${POSITION}
personality: ${PERSONALITY}
hire_date: ${HIRE_DATE}
status: active
---

# ${NAME} - ${POSITION_CN}

## 基本信息
- **ID**: ${employee_id}
- **姓名**: ${NAME}
- **性别**: ${GENDER}
- **职位**: ${POSITION_CN}（${POSITION}）
- **人格**: ${PERSONALITY_CN}（${PERSONALITY}）
- **入职日期**: ${HIRE_DATE}
- **状态**: 在职

## 工作规则
- workflow.md
- code-quality.md
- context-engineering.md

## 职位配置（内嵌）

${position_body}

## 人格配置（内嵌）

${personality_body}

---
**创建**: ${HIRE_DATE}
**更新**: ${HIRE_DATE}
EMP

  mkdir -p "$skill_dir"
  cat > "$skill_file" <<SKILL
---
name: ${command}
description: 激活员工 ${NAME} 的角色配置。用于“激活员工 ${NAME}”“启用 ${POSITION}”“${command}”等场景。
---

# Activate Employee Skill: ${NAME}

## 核心目标

激活员工档案并应用其职位与人格配置，随后按对应规则执行任务。

## 执行步骤

1. 读取员工档案：
   - ".codex/company/staff/employees/${employee_id}.md"
2. 确认员工状态为在职（\`status: active\`）。
3. 读取并遵循以下文档：
   - ".codex/company-rules/workflow.md"
   - ".codex/company-rules/code-quality.md"
   - ".codex/company-rules/context-engineering.md"
4. 以该员工角色继续执行当前任务。
SKILL

  ln -sfn "../../company/staff/employees/${employee_id}.md" "$skill_dir/employee.md"

  python3 - "$registry_file" "$employee_id" "$NAME" "$POSITION" "$PERSONALITY" "$HIRE_DATE" "$command" <<'PY'
import json
import sys
from pathlib import Path

registry_file, employee_id, name, position, personality, hire_date, command = sys.argv[1:]
path = Path(registry_file)
if path.exists():
    data = json.loads(path.read_text(encoding='utf-8'))
else:
    data = {"version": "1.0.0", "last_updated": hire_date, "employees": []}

employees = data.setdefault("employees", [])
entry = {
    "employee_id": employee_id,
    "name": name,
    "position": position,
    "personality": personality,
    "hire_date": hire_date,
    "status": "active",
    "command": command,
    "file": f".codex/company/staff/employees/{employee_id}.md"
}

updated = False
for index, item in enumerate(employees):
    if item.get("employee_id") == employee_id:
        employees[index] = entry
        updated = True
        break
if not updated:
    employees.append(entry)

data["last_updated"] = hire_date
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')
PY

  rm -f ".codex/prompts/${command}.md"

  echo "Created employee: ${employee_id}"
  echo "Skill: ${command}"
}

prepare_layout

if [[ "$MODE" == "full" || "$MODE" == "position" ]]; then
  create_position
fi
if [[ "$MODE" == "full" || "$MODE" == "personality" ]]; then
  create_personality
fi
if [[ "$MODE" == "full" ]]; then
  create_employee_and_skill
fi

echo "Done mode=$MODE"
