## Why

`src/rag_stream` 当前日志主要基于自由文本输出，字段不统一，跨路由/服务的链路追踪成本高，且部分日志存在直接输出业务文本的风险。现在需要引入 `@log_manager` 的结构化日志能力，统一关键事件与字段，提升可观测性、排障效率和日志安全性。

## What Changes

- 在 `src/rag_stream` 中引入 `@log_manager` 作为主日志输出机制，覆盖路由入口、核心服务调用、外部依赖调用与异常路径。
- 统一日志事件模型与字段规范（如 `request_id`、`chat_id`、`session_id`、`user_id`、`category`、`event`、`status`、`duration_ms`）。
- 为高风险字段增加脱敏/截断策略（例如语音文本、模型原始响应、SQL相关上下文），避免敏感信息直接落盘。
- 梳理并替换 `src/rag_stream` 关键模块中的分散日志写法，减少重复与噪声日志，保留关键诊断信号。
- 增加日志行为验证（结构字段、错误路径、关键事件完整性），确保日志升级不影响现有业务接口契约。

## Capabilities

### New Capabilities
- `rag-stream-log-manager-integration`: 规范 `src/rag_stream` 使用 `@log_manager` 的日志输出行为，包括事件定义、结构化字段、脱敏规则与关键链路覆盖要求。

### Modified Capabilities
- None.

## Impact

- Affected code: `src/rag_stream/src/routes/`, `src/rag_stream/src/services/`, `src/rag_stream/src/utils/`, `src/rag_stream/main.py`。
- Affected dependencies/systems: `src/log-manager`（日志能力来源）、现有日志配置（`.env`/`config.yaml`）与日志落盘路径。
- External API impact: 无对外接口协议变更（非 breaking），主要为可观测性与运维侧能力增强。
