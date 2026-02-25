# UPDATELOG

## 2026-02-25

### Summary
- 完成 `rag_stream` 对 `DaiShanSQL` 调用的日志增强，终端输出统一为“入参/出参”提示，结果按单行可读格式展示。
- 完成 OpenSpec 多变更归档，包含已完成与用户确认归档的未完成变更。
- 补充并通过相关回归测试，确保日志增强不改变核心业务行为。

### Major Changes
- 新增日志格式化工具：`src/rag_stream/src/utils/daishan_sql_logging.py`
- 在以下位置接入 `DaiShanSQL` 入参/出参日志：
  - `src/rag_stream/src/services/chat_general_service.py`
  - `src/rag_stream/src/services/source_dispath_srvice.py`
  - `src/rag_stream/src/utils/fetch_table_structures.py`
- 新增测试：`src/rag_stream/tests/test_daishan_sql_logging.py`

### OpenSpec
- 新增主规范：
  - `openspec/specs/daishansql-terminal-io-logging/spec.md`
  - `openspec/specs/report-function-call-chain/spec.md`
- 归档变更：
  - `openspec/changes/archive/2026-02-25-log-daishansql-io-in-rag-stream/`
  - `openspec/changes/archive/2026-02-25-adjust-report-output-call-chain/`
  - `openspec/changes/archive/2026-02-25-update-rag-stream-logging/`

### Repository Hygiene
- 更新 `.gitignore`，忽略本地运行产物目录：
  - `.log-manager/runs/`
  - `.log-manager/reports/`
