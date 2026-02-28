# Project Research Summary

**Project:** Rag Stream Query Normalization
**Domain:** rag_stream 企业名称清理型 Query 预处理
**Researched:** 2026-02-28
**Confidence:** HIGH

## Executive Summary

该需求属于 brownfield 上的“增强型预处理”改造：不改主流程结构，仅在 `handle_chat_general` 的 query 进入意图识别前插入一次企业名清理。最佳策略是新增轻量聊天适配器并接入现有 `settings` 配置体系，以最小改动完成可回滚和可测试的增强。

核心实现建议是“AI 主路径 + 原句回退”。这样既能满足“删除企业名”的语义要求，又能避免外部依赖故障影响主链路可用性。风险主要集中在 prompt 边界和配置一致性，均可通过明确约束与测试覆盖控制。

## Key Findings

### Recommended Stack

- Python + FastAPI + OpenAI SDK + Pydantic 配置模型是当前仓库最小风险方案。
- 通过 `utils` 适配层隔离 SDK 调用，避免在 service 中硬编码请求参数。

**Core technologies:**
- Python: 业务实现与测试运行 — 与现有仓库一致
- OpenAI SDK: 聊天改写调用 — 与参考实现一致
- Pydantic settings: 配置加载与 env 覆盖 — 与 rag_stream 架构一致

### Expected Features

**Must have (table stakes):**
- 企业名删除且句子其余部分尽量保持不变
- 改写失败回退原句
- 配置可控（YAML + env）

**Should have (competitive):**
- 改写前后可观测日志

**Defer (v2+):**
- 多模型路由与缓存优化

### Architecture Approach

采用 Adapter Wrapper 模式：`chat_general_service` 只调用 `utils/query_chat.py` 的单一接口。配置通过 `settings` 注入，外部失败不抛出到主流程而是回退原句。

### Critical Pitfalls

1. Prompt 过宽导致过度改写 — 通过严格约束“仅删除企业名”避免
2. 外部失败影响主链路 — 通过 fail-open 回退原句避免
3. 配置命名不一致 — 通过统一配置域与测试避免

## Implications for Roadmap

### Phase 1: 配置与边界定义
**Rationale:** 先确定配置与命名边界，避免后续返工
**Delivers:** 新配置域、加载与覆盖策略
**Addresses:** 配置一致性风险

### Phase 2: 工具实现与服务接入
**Rationale:** 在稳定配置上实现客户端并接入 replace 逻辑
**Delivers:** AI 清理企业名主路径 + 原句回退
**Uses:** OpenAI SDK 与 service 适配模式

### Phase 3: 测试与回归
**Rationale:** 验证 success/failure 双路径
**Delivers:** 单测与最小回归证据

### Phase Ordering Rationale

- 配置先行，避免工具实现后发现参数命名冲突。
- 先完成功能，再补测试回归，符合最小变更闭环。

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2:** Prompt 边界需要少量迭代

Phases with standard patterns (skip research-phase):
- **Phase 1/3:** 配置与测试均为标准工程动作

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | 完全贴合当前仓库 |
| Features | HIGH | 用户需求明确 |
| Architecture | HIGH | 改造点单一且边界清晰 |
| Pitfalls | HIGH | 可通过测试直接验证 |

**Overall confidence:** HIGH

### Gaps to Address

- 线上模型返回稳定性仍需通过真实请求观察。
- 企业名称识别准确率需后续样本回放评估。

## Sources

### Primary (HIGH confidence)
- 仓库代码：`chat_general_service.py`, `settings.py`, `OpenAI_utils.py`
- 代码库映射：`.planning/codebase/*`

---
*Research completed: 2026-02-28*
*Ready for roadmap: yes*
