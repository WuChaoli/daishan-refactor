# Roadmap: Rag Stream Query Normalization

## Overview

本路线图聚焦于在不破坏现有 `rag_stream` 主流程的前提下，引入企业名称清理型 AI 预处理能力。先完成配置与边界定义，再完成工具接入与回退策略，最后通过测试关闭回归风险。

## Phases

- [ ] **Phase 1: 配置建模** - 增加 query 清理配置域并接入 settings 加载链路。
- [ ] **Phase 2: AI 改写接入** - 新增聊天工具并接入 `replace_economic_zone`。
- [ ] **Phase 3: 测试回归** - 覆盖成功/失败路径并完成最小验证。

## Phase Details

### Phase 1: 配置建模
**Goal**: 在 `config.yaml + settings` 中建立 query 清理配置能力，命名不使用 openai 前缀。  
**Depends on**: Nothing (first phase)  
**Requirements**: [CFG-01, CFG-02]  
**Success Criteria** (what must be TRUE):
  1. `config.yaml` 中存在 query 清理配置块，命名符合约束。
  2. `Settings` 能加载该配置并支持环境变量覆盖。
  3. 未配置时服务行为可降级（不阻断主流程）。
**Plans**: 1 plan

Plans:
- [ ] 01-01: 配置模型与加载逻辑落地

### Phase 2: AI 改写接入
**Goal**: 实现聊天工具并在 `replace_economic_zone` 中调用，达到“删除企业名、保留原句”。  
**Depends on**: Phase 1  
**Requirements**: [NORM-01, NORM-02, NORM-03, SAFE-01]  
**Success Criteria** (what must be TRUE):
  1. `src/rag_stream/src/utils` 下存在新的聊天工具实现。
  2. `replace_economic_zone` 使用该工具改写 query。
  3. AI 异常时返回原 query，不再使用旧正则统一替换。
  4. 改写输出为纯文本句子。
**Plans**: 2 plans

Plans:
- [ ] 02-01: 聊天工具实现
- [ ] 02-02: service 接入与异常回退

### Phase 3: 测试回归
**Goal**: 建立最小测试证据，确保改造可回归。  
**Depends on**: Phase 2  
**Requirements**: [TEST-01, TEST-02]  
**Success Criteria** (what must be TRUE):
  1. 有针对 `handle_chat_general` 的成功路径测试。
  2. 有 AI 异常回退原句测试。
  3. 相关测试在 `.venv`/`uv` 环境可执行通过。
**Plans**: 1 plan

Plans:
- [ ] 03-01: 单测新增与执行验证

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. 配置建模 | 0/1 | Not started | - |
| 2. AI 改写接入 | 0/2 | Not started | - |
| 3. 测试回归 | 0/1 | Not started | - |
