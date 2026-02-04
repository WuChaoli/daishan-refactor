# 上下文工程规范 (Context Engineering Specification)

## 概述

上下文工程是一种结构化的文档管理系统，用于组织开发过程中的文档。它将文档分为两类：

1. **静态文档** - 长期维护的架构、API 文档
2. **开发上下文** - 按时间+功能组织的需求、计划

## 目录结构

```
docs/
├── static/                          # 静态文档（长期维护）
│   ├── architecture/                # 系统架构文档
│   │   ├── system-overview.md
│   │   ├── component-design.md
│   │   └── adr/                     # 架构决策记录
│   ├── user-journey/                # 用户旅程文档
│   ├── data-flow/                   # 数据流文档
│   ├── api/                         # API 文档
│   └── development/                 # 开发规范
│       ├── context-engineering-spec.md
│       └── context-engineering-templates.md
│
└── contexts/                        # 开发上下文（按时间+功能）
    ├── .contexts-index.json         # 全局索引
    ├── 2026-02-01_user-auth/        # 上下文目录
    │   ├── .context.json            # 元数据
    │   ├── requirements.md          # 需求文档
    │   ├── architecture-changes.md  # 架构变更
    │   ├── feature-spec.md          # 功能规格
    │   ├── plan.md                  # 实施计划
    │   ├── test-plan.md             # 测试计划
    │   ├── todos.md                 # 任务清单（可选）
    │   └── SUMMARY.md               # 归档摘要（归档时生成）
    └── 2026-02-02_api-refactor/
        └── ...
```

## 上下文 ID 格式

上下文 ID 遵循模式：`YYYY-MM-DD_feature-name`

- **日期部分**：YYYY-MM-DD 格式的创建日期
- **功能名称**：小写英文，使用连字符分隔
- **示例**：`2026-02-01_user-authentication`

## 元数据文件

### .context.json

每个上下文目录包含一个 `.context.json` 文件：

```json
{
  "contextId": "2026-02-01_user-authentication",
  "status": "in_progress",
  "createdAt": "2026-02-01T10:00:00Z",
  "updatedAt": "2026-02-01T15:30:00Z",
  "completedAt": null,
  "title": "用户认证功能",
  "description": "实现基于 JWT 的用户认证系统",
  "assignee": "developer-name",
  "gitBranch": "feature/user-auth",
  "documents": {
    "requirements": "requirements.md",
    "architectureChanges": "architecture-changes.md",
    "featureSpec": "feature-spec.md",
    "plan": "plan.md",
    "todos": "todos.md",
    "testPlan": "test-plan.md"
  },
  "staticDocsUpdated": [
    "docs/static/architecture/auth-system.md",
    "docs/static/api/auth-endpoints.md"
  ]
}
```

**字段说明：**

- `contextId`: 上下文唯一标识符
- `status`: 状态（`in_progress` | `completed`）
- `createdAt`: 创建时间（ISO 8601 格式）
- `updatedAt`: 最后更新时间
- `completedAt`: 完成时间（归档时设置）
- `title`: 功能标题（中文）
- `description`: 功能描述
- `assignee`: 负责人
- `gitBranch`: 关联的 Git 分支
- `documents`: 文档文件映射
- `staticDocsUpdated`: 此功能更新的静态文档列表

### .contexts-index.json

全局索引文件，位于 `docs/contexts/.contexts-index.json`：

```json
{
  "activeContexts": [
    {
      "contextId": "2026-02-01_user-authentication",
      "title": "用户认证功能",
      "status": "in_progress",
      "assignee": "developer-name",
      "updatedAt": "2026-02-01T15:30:00Z"
    }
  ],
  "archivedContexts": [
    {
      "contextId": "2026-01-30_api-refactor",
      "title": "API 重构",
      "status": "completed",
      "assignee": "developer-name",
      "completedAt": "2026-01-31T18:00:00Z"
    }
  ]
}
```

## 工作流程

### 1. 初始化新上下文

使用脚本创建新上下文：

```bash
python scripts/init_context.py <feature-name> [--assignee <name>] [--branch <branch-name>]
```

脚本会：
1. 生成 contextId（格式：`YYYY-MM-DD_feature-name`）
2. 创建上下文目录
3. 创建 `.context.json` 元数据文件
4. 创建初始文档（requirements.md, architecture-changes.md 等）
5. 更新 `.contexts-index.json`

### 2. 开发过程

1. 编辑上下文文档填写详情
2. 随着工作进展更新文档
3. 修改静态文档时，记录在 `.context.json` 的 `staticDocsUpdated` 中
4. 更新 `updatedAt` 时间戳

### 3. 归档上下文

使用脚本归档已完成的上下文：

```bash
python scripts/archive_context.py <context-id>
```

脚本会：
1. 设置 `status: "completed"` 和 `completedAt` 时间戳
2. 生成 `SUMMARY.md` 归档摘要
3. 将上下文从 `activeContexts` 移至 `archivedContexts`

## 文档类型

### 静态文档

长期维护的文档，按功能模块组织：

- **architecture/** - 系统架构、组件设计、ADR
- **user-journey/** - 用户旅程和交互流程
- **data-flow/** - 数据流和处理逻辑
- **api/** - API 接口文档
- **development/** - 开发规范和指南

### 上下文文档

特定功能的文档，按时间+功能组织：

- **requirements.md** - 需求文档
- **architecture-changes.md** - 架构变更
- **feature-spec.md** - 功能规格
- **plan.md** - 实施计划
- **test-plan.md** - 测试计划
- **todos.md** - 任务清单（可选）
- **SUMMARY.md** - 归档摘要（归档时生成）

## 最佳实践

1. **始终检查当前上下文** - 开始工作前读取 `.contexts-index.json`
2. **及时更新元数据** - 修改文档后更新 `updatedAt`
3. **记录静态文档变更** - 更新静态文档时添加到 `staticDocsUpdated` 数组
4. **保持文档同步** - 架构变更时同时更新动态和静态文档
5. **完整归档** - 确保 SUMMARY.md 全面准确
6. **提取经验** - 将关键经验添加到项目级文档

## 并行开发支持

上下文工程系统支持多个开发者同时处理不同功能：

- 每个功能都有自己的上下文目录
- 上下文是独立的，不会相互干扰
- 索引文件跟踪所有活跃和已归档的上下文
- 状态字段区分活跃和已完成的工作

## 工具脚本

所有脚本位于 `scripts/` 目录：

- **init_context.py** - 初始化新开发上下文
- **list_contexts.py** - 列出活跃（和已归档）上下文
- **archive_context.py** - 归档已完成上下文

## 参考

完整的文档模板请参考：`docs/static/development/context-engineering-templates.md`
