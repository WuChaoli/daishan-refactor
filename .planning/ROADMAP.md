# Roadmap: Rag Stream Intent Classification Optimization

## Overview

本路线图聚焦于引入两阶段意图识别机制，先用 LLM 进行粗粒度分类（数据库/指令/固定问题），再在对应向量库中精检索，解决语义混淆导致分类不准确的问题。

## Milestones

- ✅ **v1.0 Query Normalization** — Phases 1-4 (shipped 2026-02-28)
- ✅ **v1.1 Intent Classification Optimization** — Phases 5-8 (shipped 2026-02-28)

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

### 📋 Next Milestone (Planning)

TBD — 使用 `/gsd:new-milestone` 开始规划

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-4 | v1.0 | 5/5 | Complete | 2026-02-28 |
| 5. 意图分类基础 | v1.1 | 3/3 | Complete | 2026-02-28 |
| 6. 分类驱动检索 | v1.1 | 1/1 | Complete | 2026-02-28 |
| 8. API General 端到端测试 | v1.1 | 1/1 | Complete | 2026-02-28 |

---
*Roadmap created: 2026-02-28*
*Last updated: 2026-02-28 - v1.1 milestone archived*
