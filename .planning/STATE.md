---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Intent Classification Optimization
status: planning
last_updated: "2026-02-28T04:30:00.000Z"
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-28)

**Core value:** 用户输入中的企业名可以被稳定移除，同时保留原句其余内容不变。
**Current focus:** Defining v1.1 requirements

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-02-28 — Milestone v1.1 started

Progress: [░░░░░░░░░░░░░░░░] 0%

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

### Decisions

None yet.

### Pending Todos

None yet.

### Blockers/Concerns

- 需要设计分类 prompt，确保 LLM 准确判断类型
- 需要处理分类失败的降级逻辑
- 需要测试新流程，验证语义混淆改善效果

## Session Continuity

Last session: 2026-02-28
Stopped at: Milestone v1.0 complete
Resume file: —
