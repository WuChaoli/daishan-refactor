# Roadmap: Rag Stream Intent Classification Optimization

## Overview

本路线图聚焦于引入两阶段意图识别机制，先用 LLM 进行粗粒度分类（数据库/指令/固定问题），再在对应向量库中精检索，解决语义混淆导致分类不准确的问题。

## Milestones

- ✅ **v1.0 Query Normalization** — Phases 1-4 (shipped 2026-02-28)
- 📋 **v1.1 Intent Classification Optimization** — Phases 5-7 (planned)

## Phases

<details>
<summary>✅ v1.0 Query Normalization (Phases 1-4) — SHIPPED 2026-02-28</summary>

- [x] **Phase 1: 配置建模** — 在 `config.yaml + settings` 中建立 query 清理配置能力（1 plan）
- [x] **Phase 2: AI 改写接入** — 实现聊天工具并在 `replace_economic_zone` 中调用（2 plans）
- [x] **Phase 3: 测试回归** — 覆盖成功/失败路径并完成最小验证（1 plan）
- [x] **Phase 4: 补充真实环境测试** — 创建真实环境测试脚本和数据集（1 plan）

详见: `.planning/milestones/v1.0-ROADMAP.md`
</details>

### 📋 v1.1 Intent Classification Optimization (Planned)

- [ ] **Phase 5: 意图分类基础** — 建立粗粒度分类服务与配置体系
- [ ] **Phase 6: 分类驱动检索** — 连接分类结果与向量库检索流程
- [ ] **Phase 7: 测试验证** — 覆盖新流程的单元测试与集成测试

## Phase Details

### Phase 5: 意图分类基础

**Goal**: 建立基于 LLM 的粗粒度意图分类服务，提供稳定可靠的分类能力

**Depends on**: v1.0 (QueryChat tool exists)

**Requirements**: CLS-01, CLS-02, CLS-04, CFG-03, CFG-04

**Success Criteria** (what must be TRUE):
1. 系统在意图识别前能对用户 query 进行粗粒度分类（岱山-指令集 1 / 岱山-数据库问题 2 / 岱山-指令集-固定问题 3）
2. 分类失败或返回无效结果时，系统能降级到现有向量检索流程
3. 管理员可在 `config.yaml` 中配置分类开关、模型参数和阈值
4. 环境变量可以覆盖配置中的分类参数（如模型名称、温度）

**Plans**: 3 plans
- [ ] [05-01-PLAN.md](.planning/phases/05-意图分类基础/05-01-PLAN.md) — 意图分类服务与配置（CLS-01, CLS-02, CFG-03）
- [ ] [05-02-PLAN.md](.planning/phases/05-意图分类基础/05-02-PLAN.md) — 分类失败降级机制（CLS-04）
- [ ] [05-03-PLAN.md](.planning/phases/05-意图分类基础/05-03-PLAN.md) — 配置集成与验证（CFG-03, CFG-04）

### Phase 6: 分类驱动检索

**Goal**: 将分类结果与向量库检索流程连接，实现两阶段识别机制

**Depends on**: Phase 5

**Requirements**: CLS-03

**Success Criteria** (what must be TRUE):
1. 分类成功后，系统仅在对应类型的向量库中检索具体问题
2. 不同意图类型的查询不会跨库混淆检索结果

**Plans**: 1 plan
- [ ] [06-01-PLAN.md](.planning/phases/06-分类驱动检索/06-01-PLAN.md) — 分类驱动检索实现（CLS-03）

### Phase 7: 测试验证

**Goal**: 通过测试验证两阶段识别流程的正确性与稳定性

**Depends on**: Phase 6

**Requirements**: TEST-03, TEST-04, TEST-05

**Success Criteria** (what must be TRUE):
1. 单元测试覆盖分类成功路径（岱山-指令集 1 / 岱山-数据库问题 2 / 岱山-指令集-固定问题 3）
2. 单元测试覆盖分类失败降级路径
3. 集成测试验证两阶段识别流程从 query 输入到结果输出的完整可用性

**Plans**: TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 5. 意图分类基础 | 3/3 | Planned | - |
| 6. 分类驱动检索 | 0/1 | Planned | - |
| 7. 测试验证 | 0/0 | Not started | - |

---
*Roadmap created: 2026-02-28*
*Last updated: 2026-02-28 - Phase 6 plan created*
