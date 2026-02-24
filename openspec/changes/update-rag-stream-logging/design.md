## Context

`src/rag_stream` 当前主要通过 `log_decorator.logger` 输出自由文本日志，存在字段不统一、跨模块调用链难追踪、部分业务文本直接落盘等问题。服务包含 FastAPI 路由、异步流式返回（SSE）和多外部依赖（RAGFlow、Dify、数据库查询），属于跨模块、跨调用边界的可观测性改造。

现状还有一个技术债：测试中已有 `src.services.log_manager` 的引用，但运行时代码未提供对应实现，说明日志能力在“设计预期”和“实际接入”之间存在断层。本次设计需要在不改变对外 API 行为的前提下，完成 `@log_manager` 主导的结构化日志升级，并提供可回滚路径。

约束：
- 保持 Python 技术栈与现有工程结构；
- 配置遵循项目约定（优先 `.env`，其次 `config.yaml`）；
- 不能影响现有接口返回协议与主要业务流程；
- 重点覆盖 `src/rag_stream` 路由入口、核心服务、外部调用与异常路径。

## Goals / Non-Goals

**Goals:**
- 在 `src/rag_stream` 中建立统一的 `@log_manager` 日志接入层，输出结构化事件。
- 统一核心字段（如 `request_id`、`chat_id`、`session_id`、`user_id`、`event`、`status`、`duration_ms`）。
- 引入敏感字段治理（脱敏、截断、白名单输出）并默认启用。
- 对关键链路（`chat_routes`、`rag_service`、`source_dispath_srvice`、`personnel_dispatch_service`、`dify_service`、`ragflow_client`）完成优先覆盖。
- 提供灰度和回滚机制，保证迁移期间可控。

**Non-Goals:**
- 不重构业务算法、意图识别策略或数据库查询逻辑。
- 不调整对外 HTTP API 协议与字段。
- 不在本阶段完成全仓库日志框架统一（仅聚焦 `src/rag_stream`）。

## Decisions

### 1) 引入日志适配层（Facade）而非直接全量替换

**Decision:** 新增 `src/rag_stream/src/observability/logging_adapter.py`（命名可在实现阶段微调），对外提供统一 API（如 `log_event()`、`log_error()`、`bind_context()`），内部封装 `log_manager` 的 `configure / entry_trace / trace / marker`。

**Rationale:** 现有代码大量使用 `logger.info(...)`，直接一刀切替换会造成高改动风险；适配层可以先承接结构化字段与敏感信息治理，再逐步替换调用点。

**Alternatives considered:**
- 方案 A：逐文件直接改成 `@entry_trace/@trace` + `marker`（改动面最大，回归风险高）。
- 方案 B：继续用 `log_decorator`，仅规范文案（无法满足结构化与统一治理目标）。

### 2) 请求级上下文使用 `contextvars` + FastAPI 中间件

**Decision:** 在 FastAPI 中间件中生成/提取 `request_id`，并将 `request_id/user_id/session_id/category` 写入上下文容器；日志适配层自动合并上下文字段。

**Rationale:** 避免在每个函数签名中传递日志上下文，减少侵入并保证异步链路可追踪。

**Alternatives considered:**
- 手工参数透传（样板代码多、易遗漏）。
- 仅在路由层记录上下文（服务层与工具层链路会丢失关键信息）。

### 3) 敏感信息治理采用“白名单字段 + 定长截断 + 错误详情分级”

**Decision:**
- 默认不记录原始长文本（如 `voice_text`、模型完整输出、SQL原文）；
- 对必要文本字段只记录长度、哈希或前后缀片段；
- 异常日志拆分为“对外可见摘要”和“内部诊断详情”。

**Rationale:** 满足排障与安全的平衡，避免自由文本日志造成隐私和合规风险。

**Alternatives considered:**
- 全量打码（诊断价值不足）。
- 黑名单模式（易漏配，长期维护风险高）。

### 4) 采用三阶段迁移：`legacy -> dual -> log_manager`

**Decision:** 增加运行模式开关（建议 `.env`：`RAG_STREAM_LOG_MODE=legacy|dual|log_manager`）。
- `legacy`: 仅旧日志
- `dual`: 旧日志 + `log_manager` 并行输出
- `log_manager`: 仅新日志

**Rationale:** 渐进发布可降低观测盲区风险，并支持快速回滚。

**Alternatives considered:**
- 一次性切换到新日志（上线风险不可控）。

### 5) 先补“兼容实现”再推进替换

**Decision:** 为测试中既有的 `src.services.log_manager` 引用提供兼容入口（可为 shim/adapter），避免测试与运行时分裂。

**Rationale:** 当前测试依赖与运行时代码不一致，先对齐可降低后续改造噪声并提高验证效率。

**Alternatives considered:**
- 先改所有测试再改实现（工作量大且反馈周期长）。

## Risks / Trade-offs

- [Risk] `log_manager` 在高频流式场景下产生额外开销  
  -> Mitigation: 仅记录关键事件，内容分块不逐块打点；采用采样和阈值触发报告。

- [Risk] 双写阶段日志量激增、检索噪声变大  
  -> Mitigation: `dual` 模式限时使用，按模块分批切换并设置观察窗口。

- [Risk] 异步链路上下文丢失导致字段不完整  
  -> Mitigation: 使用中间件 + contextvars + 关键边界显式 `bind_context()`。

- [Risk] 脱敏规则过严影响排障，过松带来泄露风险  
  -> Mitigation: 建立字段分级表，优先白名单；在测试中加入“敏感字段不落盘”断言。

- [Risk] 现有测试基于旧日志行为，迁移期间易误报  
  -> Mitigation: 将测试拆为“业务行为断言”和“日志契约断言”，减少对具体文案的耦合。

## Migration Plan

1. **基线准备**：在 `rag_stream` 增加日志模式配置与 `log_manager` 运行时初始化（应用启动、优雅关闭时 flush/shutdown）。
2. **适配层落地**：新增 observability 适配模块，提供统一日志 API 与敏感字段处理工具。
3. **上下文注入**：增加 FastAPI 中间件生成 `request_id` 并绑定请求上下文。
4. **关键链路改造**：按模块批次替换日志调用（先 routes + core services，再 utils）。
5. **测试补齐**：新增/更新日志契约测试（字段完整性、错误事件、脱敏规则、关键事件覆盖）。
6. **灰度切换**：`legacy -> dual -> log_manager`，每阶段观察错误率、请求时延、日志有效性。
7. **收敛清理**：稳定后移除冗余旧日志路径，保留必要兼容层。

**Rollback Strategy:**
- 通过 `.env` 将 `RAG_STREAM_LOG_MODE` 回切至 `legacy`；
- 保留旧日志调用在 dual 阶段直至验证完成；
- 回滚不涉及 API 协议与数据模型迁移，属于可快速切换。

## Open Questions

- `log_manager` 输出目录是否采用默认 `.log-manager/`，还是对齐现有 `rag_stream` 日志目录策略？
- 敏感字段白名单最终由谁维护（研发/运维/安全）以及审批机制是什么？
- `entry_trace/trace` 对当前异步流式函数边界的覆盖策略是“函数级全覆盖”还是“关键路径优先”？
- 旧 `log_decorator` 兼容窗口保留多久，退出条件如何量化（例如稳定运行天数、错误率阈值）？
