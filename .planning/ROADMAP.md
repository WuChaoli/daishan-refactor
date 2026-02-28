# Roadmap: Rag Stream Integration Testing for CI/CD

## Overview

本路线图聚焦于构建 CI/CD 集成测试套件，使用 .venv 环境连接外部真实环境，验证接口连通性，支持自动化测试流水线。

## Milestones

- ✅ **v1.0 Query Normalization** — Phases 1-4 (shipped 2026-02-28)
- ✅ **v1.1 Intent Classification Optimization** — Phases 5-8 (shipped 2026-02-28)
- ○ **v1.2 Integration Testing for CI/CD** — Phases 9-11 (in progress)

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

- [ ] **Phase 9: 外部服务连通性测试** — 验证 AI API、向量库、数据库连通性（1 plan）
  - Requirements: INT-01, INT-02, INT-03, INT-04
  - Success Criteria: 所有外部服务连通性测试通过，失败时提供诊断信息

- [ ] **Phase 10: API E2E 测试** — 完整 API 流程测试与配置分离（1 plan）
  - Requirements: INT-05, INT-06
  - Success Criteria: /api/general 接口完整流程测试通过，配置可环境注入

- [ ] **Phase 11: CI/CD 流水线集成** — 测试报告与流水线配置（1 plan）
  - Requirements: INT-07, INT-08
  - Success Criteria: GitHub Actions 工作流可正常运行，生成 JUnit 报告

</details>

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-4 | v1.0 | 5/5 | Complete | 2026-02-28 |
| 5. 意图分类基础 | v1.1 | 3/3 | Complete | 2026-02-28 |
| 6. 分类驱动检索 | v1.1 | 1/1 | Complete | 2026-02-28 |
| 8. API General 端到端测试 | v1.1 | 1/1 | Complete | 2026-02-28 |
| 9. 外部服务连通性测试 | v1.2 | 0/1 | Pending | — |
| 10. API E2E 测试 | v1.2 | 0/1 | Pending | — |
| 11. CI/CD 流水线集成 | v1.2 | 0/1 | Pending | — |

---
*Roadmap created: 2026-02-28*
*Last updated: 2026-02-28 - v1.2 roadmap created*
