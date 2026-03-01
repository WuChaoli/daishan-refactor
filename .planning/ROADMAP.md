# Roadmap: Rag Stream Integration Testing for CI/CD

## Overview

本路线图聚焦于构建 CI/CD 集成测试套件，使用 .venv 环境连接外部真实环境，验证接口连通性，支持自动化测试流水线。

## Milestones

- ✅ **v1.0 Query Normalization** — Phases 1-4 (shipped 2026-02-28)
- ✅ **v1.1 Intent Classification Optimization** — Phases 5-8 (shipped 2026-02-28)
- ○ **v1.2 Integration Testing for CI/CD** — Phases 9-11 (in progress)
- ○ **v1.3 Production Build and Deployment Scripts** — Phases 12-15 (planned)

## Phases

<details>
<summary>✅ v1.0 Query Normalization (Phases 1-4) — SHIPPED 2026-02-28</summary>

- [x] **Phase 1: 配置建模** — 在 `config.yaml + settings` 中建立 query 清理配置能力（1 plan）
- [x] **Phase 2: AI 改写接入** — 实现聊天工具并在 `replace_economic_zone` 中调用（2 plans）
- [x] **Phase 3: 测试回归** — 覆盖成功/失败路径并完成最小验证（1 plan）
- [x] **Phase 4: 补充真实环境测试** — 创建真实环境测试脚本和数据集（1 plan）

详见: `.planning/milestones/v1.0-ROADMAP.md`
</details>

<details>
<summary>✅ v1.1 Intent Classification Optimization (Phases 5-8) — SHIPPED 2026-02-28</summary>

- [x] **Phase 5: 意图分类基础** — 建立粗粒度分类服务与配置体系（3 plans）
- [x] **Phase 6: 分类驱动检索** — 连接分类结果与向量库检索流程（1 plan）
- [x] **Phase 8: API General 端到端测试** — 创建 E2E 测试验证完整流程（1 plan）

详见: `.planning/milestones/v1.1-ROADMAP.md`
</details>

<details>
<summary>○ v1.2 Integration Testing for CI/CD (Phases 9-11) — IN PROGRESS</summary>

- [x] **Phase 9: 外部服务连通性测试** — 验证 AI API、向量库、数据库连通性（1 plan） (completed 2026-02-28)
  - Requirements: INT-01, INT-02, INT-03, INT-04
  - Success Criteria: 所有外部服务连通性测试通过，失败时提供诊断信息
  - Plans:
    - [x] 09-01-PLAN.md — 创建外部服务连通性测试套件

- [x] **Phase 10: API E2E 测试** — 完整 API 流程测试与配置分离（2 plans）(completed 2026-02-28)
  - Requirements: INT-05, INT-06
  - Success Criteria: /api/general 接口完整流程测试通过，配置可环境注入
  - Plans:
    - [x] 10-01-PLAN.md — 创建 CI/CD 就绪的 E2E 测试套件（pytest + Docker Compose + GitHub Actions）
    - [ ] 10-02-PLAN.md — Gap Closure: 添加意图分类解析逻辑和测试数据（gap closure from verification）

- [ ] **Phase 11: CI/CD 流水线集成** — 测试报告与流水线配置（1 plan）
  - Requirements: INT-07, INT-08
  - Success Criteria: GitHub Actions 工作流可正常运行，生成 JUnit 报告

</details>

<details>
<summary>○ v1.3 Production Build and Deployment Scripts (Phases 12-15) — PLANNED</summary>

- [x] **Phase 12: Docker Containerization** — 安全优化的容器配置（2 plans）
  - Requirements: DOCKER-01, DOCKER-02
  - Success Criteria: 多阶段构建成功、非 root 运行、优雅关闭、无 secrets 泄漏
  - Plans:
    - [x] 12-01-PLAN.md — Create Production Dockerfile (2026-02-28)
    - [x] 12-02-PLAN.md — Docker Compose Configuration (2026-02-28)

- [x] **Phase 13: Service Lifecycle Management** — 启动关闭与资源清理（1 plan） (completed 2026-03-01)
  - Requirements: LIFECYCLE-01, LIFECYCLE-02
  - Success Criteria: SIGTERM 正确处理、连接优雅关闭、启动脚本可靠
  - Plans:
    - [ ] 13-01-PLAN.md — Implement comprehensive service lifecycle management with FastAPI lifespan, graceful shutdown, and resource cleanup

- [ ] **Phase 14: Health Checks & Monitoring** — 编排器就绪健康端点（1 plan）
  - Requirements: HEALTH-01, HEALTH-02
  - Success Criteria: /health 轻量检查、/health/ready 依赖验证、HTTP 状态码正确

- [ ] **Phase 15: Log Management** — 容器原生日志与轮转（1 plan）
  - Requirements: LOG-01, LOG-02
  - Success Criteria: stdout 日志、JSON 结构化、Docker 轮转配置、级别可控

</details>

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-4 | v1.0 | 5/5 | Complete | 2026-02-28 |
| 5. 意图分类基础 | v1.1 | 3/3 | Complete | 2026-02-28 |
| 6. 分类驱动检索 | v1.1 | 1/1 | Complete | 2026-02-28 |
| 8. API General 端到端测试 | v1.1 | 1/1 | Complete | 2026-02-28 |
| 9. 外部服务连通性测试 | v1.2 | 1/1 | Complete | 2026-02-28 |
| 10. API E2E 测试 | 2/2 | Complete    | 2026-02-28 | 2026-02-28 |
| 11. CI/CD 流水线集成 | v1.2 | 0/1 | Pending | — |
| 12. Docker Containerization | v1.3 | 2/2 | Complete | 2026-02-28 |
| 13. Service Lifecycle Management | 1/1 | Complete    | 2026-03-01 | 2026-03-01 |
| 14. Health Checks & Monitoring | v1.3 | 0/1 | Planned | — |
| 15. Log Management | v1.3 | 0/1 | Planned | — |

### Phase 9: 外部服务连通性测试

**Goal:** 验证 AI API、向量库、数据库连通性

**Requirements:** INT-01, INT-02, INT-03, INT-04

**Success Criteria:**
- AI API 连通性测试通过（实际调用验证）
- 向量库连通性测试通过（实际检索验证）
- 数据库连通性测试通过（实际查询验证）
- 失败时提供清晰的诊断信息

### Phase 10: API E2E 测试

**Goal:** 完整 API 流程测试与配置分离

**Requirements:** INT-05, INT-06

**Success Criteria:**
- /api/general 接口完整流程测试通过
- 配置支持环境变量注入
- 测试可在 CI/CD 环境中运行

### Phase 11: CI/CD 流水线集成

**Goal:** 测试报告与流水线配置

**Requirements:** INT-07, INT-08

**Success Criteria:**
- GitHub Actions 工作流可正常运行
- 生成 JUnit/XML 格式报告
- 测试失败时通知机制

### Phase 12: Docker Containerization

**Goal:** 安全优化的容器配置

**Requirements:** DOCKER-01, DOCKER-02

**Success Criteria:**
- Docker image builds with multi-stage uv build
- Container runs as non-root user (UID ≥ 1000)
- Graceful shutdown on SIGTERM within 5 seconds
- No secrets in image layers (`docker history` clean)
- Image size under 500MB

**Plans:**
2/2 plans complete
- ✅ **12-02: Docker Compose Configuration** — Service orchestration, health checks, resource limits, graceful shutdown (2026-02-28)

### Phase 13: Service Lifecycle Management

**Goal:** 启动关闭与资源清理

**Requirements:** LIFECYCLE-01, LIFECYCLE-02

**Success Criteria:**
- SIGTERM triggers proper cleanup sequence
- Lifespan shutdown closes external connections
- Startup script handles database wait/initialization
- Uvicorn configured with 4 workers + 30s timeout
- Container restart policy configured

### Phase 14: Health Checks & Monitoring

**Goal:** 编排器就绪健康端点

**Requirements:** HEALTH-01, HEALTH-02

**Success Criteria:**
- GET `/health` responds in <100ms with 200 OK
- GET `/health/ready` validates RAGFlow connectivity
- Proper HTTP status codes (200/503)
- Docker HEALTHCHECK passes during normal operation
- Health response includes dependency status

### Phase 15: Log Management

**Goal:** 容器原生日志与轮转

**Requirements:** LOG-01, LOG-02

**Success Criteria:**
- Logs output to stdout/stderr (visible via `docker logs`)
- No file logging in container filesystem
- Docker log rotation configured (10MB max, 3 files)
- Structured JSON format
- Log level configurable via env var

---
*Roadmap created: 2026-02-28*
*Last updated: 2026-03-01 - Completed Phase 13 Planning*
