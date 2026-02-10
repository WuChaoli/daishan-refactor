---
name: comp-hire-employee
description: "一键创建职位模板 + 人格模板 + 员工档案 + activate 技能。用于“招聘员工”“一键创建员工体系”“hire employee”场景。"
---

# Company One-shot Creator

目标：**一个命令完成全链路创建**（职位 + 人格 + 员工 + 激活技能）。

## 一键命令

```bash
bash .codex/company/tools/bootstrap_employee.sh \
  --name 王麻子 \
  --position test-engineer \
  --position-cn 测试工程师 \
  --department 技术部 \
  --personality analytical-type \
  --personality-cn 分析型 \
  --gender 男 \
  --hire-date 2026-02-10
```

## 目录编排（唯一结构）

```text
.codex/company/
├── catalog/
│   ├── positions/
│   └── personalities/
├── staff/
│   └── employees/
└── tools/
    └── bootstrap_employee.sh
```

## 输入参数

必需：
- `--name`
- `--position` / `--position-cn`
- `--personality` / `--personality-cn`

可选：
- `--department`（默认：技术部）
- `--gender`（默认：男）
- `--hire-date`（默认：当天）
- `--position-brief`
- `--personality-traits`

## 产物清单

- 职位模板：`.codex/company/catalog/positions/<position>.md`
- 人格模板：`.codex/company/catalog/personalities/<personality>.md`
- 员工档案：`.codex/company/staff/employees/<position>-<name>.md`
- 员工注册表：`.codex/company/staff/employees/.employees-registry.json`
- 激活技能：`.codex/skills/activate-<position>-<name>/SKILL.md`
- 软链接：`.codex/skills/activate-<position>-<name>/employee.md`

## 校验清单

- 员工档案已内嵌职位与人格正文
- 注册表记录存在且 `command=activate-<position>-<name>`
- 激活技能与软链接可访问
