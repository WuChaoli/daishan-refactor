# Company Layout

## Canonical Structure

```text
.codex/company/
├── catalog/
│   ├── positions/       # 职位模板
│   └── personalities/   # 人格模板
├── staff/
│   └── employees/       # 员工档案与注册表
└── tools/
    └── bootstrap_employee.sh  # 一键创建入口
```

## One-command Provisioning

使用以下命令一次性创建职位 + 人格 + 员工 + 激活技能：

```bash
bash .codex/company/tools/bootstrap_employee.sh \
  --name 张三 \
  --position data-engineer \
  --position-cn 数据工程师 \
  --department 技术部 \
  --personality analytical-type \
  --personality-cn 分析型
```
