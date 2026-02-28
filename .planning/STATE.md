---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Intent Classification Optimization
status: unknown
last_updated: "2026-02-28T06:18:56.952Z"
progress:
  total_phases: 6
  completed_phases: 6
  total_plans: 9
  completed_plans: 9
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-28)

**Core value:** 用户输入中的企业名可以被稳定移除，同时保留原句其余内容不变。
**Current focus:** Implementing v1.1 intent classification optimization

## Current Position

Phase: 06-分类驱动检索
Plan: 06-01
Status: Completed classification-driven retrieval implementation
Last activity: 2026-02-28 — Completed plan 06-01

Progress: [████████████████░░] 100% (1/1 plans)

## Accumulated Context

### Previous Milestone Context

**v1.0 Query Normalization (Completed 2026-02-28)**
- 实现了企业名称清理的 AI 预处理链路
- 4 个阶段全部完成，5 个计划交付
- 新增 `QueryChat` 工具类，配置模型集成

### Current Milestone Context

**核心问题：意图分类不准确**
- 案例：「XX企业的危化品类目」本应归属数据库问题，但指令集也返回高阈值（>0.7）
- 原因：不同意图类型的问题在向量空间中语义接近
- 影响：检索结果混淆，错误的向量库被选中

**拟议方案：两阶段识别**
1. 粗分类：LLM 判断问题类型（数据库 0 / 指令 1 / 固定问题 2）
2. 精检索：仅在对应类型的向量库中检索具体问题
3. 工具复用：使用现有 `QueryChat` 实现，新增分类 prompt 配置

**Roadmap 结构：**
- Phase 5: 意图分类基础（CLS-01, CLS-02, CLS-04, CFG-03, CFG-04）✅
- Phase 6: 分类驱动检索（CLS-03）✅
- Phase 7: 测试验证（TEST-03, TEST-04, TEST-05）

### Decisions

- **Classifier initialization wrapped in try/except** to prevent blocking main flow on startup failures (05-03)
- **Phase 5 only completes integration preparation**; actual classification calls deferred to Phase 6 (05-03)
- **Config validation logs warnings** instead of raising exceptions for missing fields (05-03)
- **Use dataclasses.replace for immutable settings update** when filtering database_mapping (06-01)
- **Keep backward compatibility** with optional text_input parameter defaulting to None (06-01)
- **Defensive programming**: return full mapping when no matching database found (06-01)

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-02-28T06:26:00Z
Stopped at: Completed 06-01-PLAN.md - Classification-Driven Retrieval
Resume file: .planning/phases/06-分类驱动检索/06-01-SUMMARY.md
