## Why

`rag_stream` 内部多处调用 `DaiShanSQL`，但目前缺少统一、可检索的终端日志来展示调用入参与出参结果，排查 SQL 生成错误、接口返回异常、以及路由分支问题成本较高。需要在不改变业务语义的前提下，补齐可观测性，支持快速定位问题。

## What Changes

- 在 `rag_stream` 中为 `DaiShanSQL` 调用建立统一的终端日志输出规范，覆盖调用前入参和调用后出参。
- 日志实现统一基于现有 `log_manager`（`marker` / `trace` / `entry_trace`）能力，保持与项目现有代码风格一致。
- 覆盖 `src/rag_stream` 下所有实际业务代码中的 `DaiShanSQL` 调用点，包括 `QueryBySQL`、`get_sql_result`、`judgeQuery` 及 `sqlFixed` 相关调用。
- 日志包含最小必要字段：调用点、方法名、关键入参摘要、返回结果摘要、耗时、调用是否成功。
- 对异常路径输出统一错误日志，确保失败时也能看到入参与错误信息。
- 对大文本/复杂对象进行安全裁剪与序列化，避免日志不可读或输出过大。

## Capabilities

### New Capabilities
- `daishansql-terminal-io-logging`: 为 `rag_stream` 中所有 `DaiShanSQL` 调用提供统一、可读、可追踪的终端入参/出参日志。

### Modified Capabilities
- None.

## Impact

- Affected code:
  - `src/rag_stream/src/services/chat_general_service.py`
  - `src/rag_stream/src/services/source_dispath_srvice.py`
  - `src/rag_stream/src/utils/fetch_table_structures.py`（若纳入运行路径/脚本路径）
- Logging/observability:
  - 终端日志会新增 `DaiShanSQL` 调用链相关输出，便于本地和联调排障。
- Runtime behavior:
  - 不改变业务决策逻辑，仅增加日志输出与异常可观测性。
