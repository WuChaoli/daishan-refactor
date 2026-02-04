# 上下文工程系统使用指南

本项目使用上下文工程系统来管理开发文档。

## 快速开始

### 1. 查看当前活跃的上下文

```bash
python scripts/list_contexts.py
```

### 2. 开始新功能开发

```bash
python scripts/init_context.py <feature-name> --assignee <your-name> --branch <branch-name>
```

示例：
```bash
python scripts/init_context.py user-authentication --assignee developer --branch feature/user-auth
```

这将创建：
- 上下文目录：`docs/contexts/YYYY-MM-DD_feature-name/`
- 元数据文件：`.context.json`
- 初始文档：requirements.md, architecture-changes.md, feature-spec.md, plan.md, test-plan.md, todos.md

### 3. 开发过程中

1. 编辑上下文文档填写详情
2. 随着工作进展更新文档
3. 修改静态文档时，记录在 `.context.json` 的 `staticDocsUpdated` 中

### 4. 完成功能后归档

```bash
python scripts/archive_context.py <context-id>
```

示例：
```bash
python scripts/archive_context.py 2026-02-01_user-authentication
```

这将：
- 设置状态为 `completed`
- 生成 `SUMMARY.md` 归档摘要
- 将上下文从活跃移至已归档

## 目录结构

```
docs/
├── static/                          # 静态文档（长期维护）
│   ├── architecture/                # 系统架构文档
│   ├── user-journey/                # 用户旅程文档
│   ├── data-flow/                   # 数据流文档
│   ├── api/                         # API 文档
│   └── development/                 # 开发规范
│       ├── context-engineering-spec.md
│       └── context-engineering-templates.md
│
└── contexts/                        # 开发上下文（按时间+功能）
    ├── .contexts-index.json         # 全局索引
    └── YYYY-MM-DD_feature-name/     # 上下文目录
        ├── .context.json            # 元数据
        ├── requirements.md          # 需求文档
        ├── architecture-changes.md  # 架构变更
        ├── feature-spec.md          # 功能规格
        ├── plan.md                  # 实施计划
        ├── test-plan.md             # 测试计划
        ├── todos.md                 # 任务清单
        └── SUMMARY.md               # 归档摘要（归档时生成）
```

## 脚本说明

### init_context.py

初始化新的开发上下文。

```bash
python scripts/init_context.py <feature-name> [选项]

选项:
  --assignee <name>      负责人姓名（默认：developer）
  --branch <branch>      Git 分支名称（默认：feature/<feature-name>）
  --title <title>        功能标题（中文）
  --description <desc>   功能描述
```

### list_contexts.py

列出活跃和已归档的开发上下文。

```bash
python scripts/list_contexts.py [选项]

选项:
  --all    列出所有上下文（包括已归档）
```

### archive_context.py

归档已完成的开发上下文。

```bash
python scripts/archive_context.py <context-id>
```

## 最佳实践

1. **始终检查当前上下文** - 开始工作前运行 `list_contexts.py`
2. **及时更新元数据** - 修改文档后更新 `.context.json` 中的 `updatedAt`
3. **记录静态文档变更** - 更新静态文档时添加到 `staticDocsUpdated` 数组
4. **保持文档同步** - 架构变更时同时更新动态和静态文档
5. **完整归档** - 确保 SUMMARY.md 全面准确
6. **提取经验** - 将关键经验添加到项目级文档

## 详细文档

- **完整规范**: `docs/static/development/context-engineering-spec.md`
- **文档模板**: `docs/static/development/context-engineering-templates.md`

## 示例工作流

```bash
# 1. 查看当前活跃的上下文
python scripts/list_contexts.py

# 2. 开始新功能
python scripts/init_context.py api-refactor --assignee developer --branch feature/api-refactor

# 3. 编辑文档
# 编辑 docs/contexts/2026-02-01_api-refactor/requirements.md
# 编辑 docs/contexts/2026-02-01_api-refactor/plan.md
# ...

# 4. 开发过程中更新文档
# 更新 .context.json 中的 updatedAt 和 staticDocsUpdated

# 5. 完成后归档
python scripts/archive_context.py 2026-02-01_api-refactor

# 6. 完善归档摘要
# 编辑 docs/contexts/2026-02-01_api-refactor/SUMMARY.md
```

## 故障排除

### 上下文已存在

如果尝试创建已存在的上下文，脚本会报错。可以：
- 使用不同的功能名称
- 或使用现有上下文

### 索引文件缺失

如果 `.contexts-index.json` 不存在，初始化第一个上下文时会自动创建。

### 元数据损坏

如果元数据文件损坏，参考 `context-engineering-spec.md` 中的格式手动重新创建。
