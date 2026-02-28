# Roadmap: Rag Stream Query Normalization

## Overview

本路线图聚焦于在不破坏现有 `rag_stream` 主流程的前提下，引入企业名称清理型 AI 预处理能力。先完成配置与边界定义，再完成工具接入与回退策略，最后通过测试关闭回归风险。

## Milestones

- ✅ **v1.0 Query Normalization** — Phases 1-4 (shipped 2026-02-28)
- 📋 **v1.1** — Planning

## Phases

<details>
<summary>✅ v1.0 Query Normalization (Phases 1-4) — SHIPPED 2026-02-28</summary>

- [x] **Phase 1: 配置建模** — 在 `config.yaml + settings` 中建立 query 清理配置能力（1 plan）
- [x] **Phase 2: AI 改写接入** — 实现聊天工具并在 `replace_economic_zone` 中调用（2 plans）
- [x] **Phase 3: 测试回归** — 覆盖成功/失败路径并完成最小验证（1 plan）
- [x] **Phase 4: 补充真实环境测试** — 创建真实环境测试脚本和数据集（1 plan）

详见: `.planning/milestones/v1.0-ROADMAP.md`
</details>

### 📋 v1.1 [Name] (Planned)
