---
name: doc-location-manager
description: 文档位置管理系统，用于组织和维护项目文档的目录结构。当用户需要创建文档、组织文档结构、查找文档位置、或提到"docs目录"、"文档位置"、"静态文档"、"开发上下文"、"归档文档"时使用。支持静态文档(docs/static/)和动态文档(docs/contexts/)的两层管理架构，提供文档索引、元数据管理和归档工作流。
---

# Doc Location Manager

## 核心原则

本项目使用两层文档管理架构：

1. **静态文档** (`docs/static/`) - 长期维护的架构、API、指南文档
2. **开发上下文** (`docs/contexts/`) - 按时间+功能组织的动态需求文档

## 目录结构

```
project/
├── docs/
│   ├── static/                    # 静态文档（长期维护）
│   │   ├── architecture/          # 架构文档
│   │   ├── design/                # 设计文档
│   │   ├── api/                   # API 接口文档
│   │   ├── guide/                 # 使用/部署手册
│   │   └── spec/                  # 需求规格/验收
│   │
│   ├── contexts/                  # 开发上下文（按时间+功能）
│   │   ├── .contexts-index.json  # 上下文索引
│   │   └── YYYY-MM-DD_feature-name/
│   │       ├── .context.json     # 元数据
│   │       ├── requirements.md   # 需求文档
│   │       ├── feature-spec.md   # 功能规格
│   │       ├── plan.md           # 实施计划
│   │       └── SUMMARY.md        # 归档总结
│   │
│   └── archive/                   # 已归档文档（只读）
│
└── CLAUDE.md                      # 项目级配置
```

## 快速参考

### 静态文档分类

| 目录 | 用途 | 示例 |
|------|------|------|
| `architecture/` | 系统架构、组件设计 | system-architecture.md |
| `design/` | 模块设计、数据流 | user-journey.md |
| `api/` | 接口定义、协议 | user-api.md |
| `guide/` | 使用、部署手册 | deployment-guide.md |
| `spec/` | 需求规格、验收 | feature-requirements.md |

### 动态文档组织

**Context ID 格式**: `YYYY-MM-DD_feature-name` (英文小写+下划线)

**根目录文档**（功能级别）:
- `requirements.md` - 需求文档
- `feature-spec.md` - 功能规格
- `plan.md` - 实施计划
- `todos.md` - 任务清单
- `SUMMARY.md` - 归档总结（完成后生成）

**职位相关文档**（直接放在根目录）:
- 需求规划师：`requirement.md`, `user-story.md`, `acceptance.md`, `flow.md`
- 架构师：`design.md`, `diff.md`, `sync.md`
- TDD开发工程师：`task-breakdown.md`, `test-cases.md`, `dev-log.md`, `test-report.md`
- 重构工程师：`baseline.md`, `plan.md`, `progress.md`, `comparison.md`, `summary.md`, `tests/`
- 测试工程师：`test-cases.md`, `execution-log.md`, `error-analysis.md`, `summary.md`

**完整示例**:
```
docs/contexts/2026-02-04_user-auth/
├── requirements.md              # 功能需求
├── requirement.md               # 需求文档（需求规划师）
├── user-story.md                # 用户故事
├── acceptance.md                # 验收标准
├── flow.md                      # 流程图
├── design.md                    # 架构设计
├── diff.md                      # 差异分析
├── sync.md                      # 同步报告
├── task-breakdown.md            # 任务拆解
├── test-cases.md                # 测试用例
├── dev-log.md                   # 开发日志
├── test-report.md               # 测试报告
├── baseline.md                  # 重构基线
├── refactor-plan.md             # 重构方案
├── progress.md                  # 进度跟踪
├── comparison.md                # 测试对比
├── tests/                       # 测试代码目录
│   ├── test_*.py
│   └── fixtures/
├── execution-log.md             # 执行日志
├── error-analysis.md            # 错误分析
├── summary.md                   # 总结文档
└── .context.json                # 元数据
```

## 常见操作

### 创建新上下文

```
docs/contexts/YYYY-MM-DD_feature-name/
```

1. 创建目录
2. 创建 `.context.json` 元数据文件
3. 创建功能级别文档
4. 更新 `.contexts-index.json`

### 创建静态文档

```
docs/static/[category]/document-name.md
```

选择合适的 category：architecture, design, api, guide, spec

### 归档上下文

1. 生成 `SUMMARY.md` 总结文档
2. 更新 `.context.json` 状态为 `archived`
3. 更新 `.contexts-index.json` 移至 `archivedContexts`
4. 归档：移动到 `docs/archive/`

### 查找文档

- **活跃上下文**: 读取 `docs/contexts/.contexts-index.json`
- **上下文元数据**: 读取 `docs/contexts/[contextId]/.context.json`
- **静态文档**: 浏览 `docs/static/` 目录

## 元数据格式

### .context.json

```json
{
  "contextId": "2026-01-20_user-authentication",
  "status": "in_progress",
  "createdAt": "2026-01-20T10:00:00Z",
  "updatedAt": "2026-01-20T15:30:00Z",
  "completedAt": null,
  "title": "用户认证功能",
  "description": "实现基于 JWT 的用户认证系统",
  "assignee": "developer-name",
  "gitBranch": "feature/user-auth",
  "documents": {
    "requirements": "requirements.md",
    "featureSpec": "feature-spec.md",
    "plan": "plan.md"
  },
  "staticDocsUpdated": []
}
```

### .contexts-index.json

```json
{
  "activeContexts": [
    {
      "contextId": "2026-01-20_user-authentication",
      "title": "用户认证功能",
      "status": "in_progress",
      "assignee": "developer-name",
      "updatedAt": "2026-01-20T15:30:00Z"
    }
  ],
  "archivedContexts": []
}
```

## 最佳实践

1. **始终检查当前上下文** - 读取 `.contexts-index.json` 确认活跃上下文
2. **及时更新元数据** - 修改文档后更新 `.context.json` 的 `updatedAt`
3. **记录静态文档变更** - 在 `staticDocsUpdated` 中记录所有变更
4. **完整的归档** - 归档时确保生成完整的 `SUMMARY.md`
5. **Context ID 命名** - 使用英文小写+下划线，格式为 `YYYY-MM-DD_feature-name`
6. **文档直接放置** - 所有文档直接放在特性根目录，无需创建子目录层级
7. **文件命名清晰** - 使用描述性文件名，避免冲突（如：`refactor-plan.md` vs `test-plan.md`）
