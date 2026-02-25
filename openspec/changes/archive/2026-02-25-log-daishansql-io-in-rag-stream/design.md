## Context

当前 `rag_stream` 已接入 `log-manager`，但 `DaiShanSQL` 调用的入参/出参日志分散且不完整：
- `chat_general_service.py` 中存在 `sqlFixed`、`get_sql_result`、`judgeQuery` 调用，缺少统一输入输出记录。
- `source_dispath_srvice.py` 中 `QueryBySQL` 调用仅记录了部分结果类型，没有记录关键入参与结果摘要。
- `fetch_table_structures.py` 采用 `print` 输出，格式与主服务日志不一致。

该变更是横跨多个模块的可观测性改造，需要统一日志结构并确保不改变现有业务路由语义。

## Goals / Non-Goals

**Goals:**
- 为 `src/rag_stream` 下全部 `DaiShanSQL` 调用建立统一终端日志格式，输出调用入参与出参摘要。
- 覆盖成功、空结果、异常三类路径，并输出耗时与调用结果状态。
- 保持业务行为不变：仅增强日志，不改变 SQL 执行结果与路由策略。
- 对超长文本和复杂对象做可读裁剪，防止日志爆量。

**Non-Goals:**
- 不重构 `DaiShanSQL` SDK 内部实现。
- 不修改业务 SQL 语句逻辑、Dify 提示词策略或路由分支逻辑。
- 不引入新的外部日志依赖。

## Decisions

### Decision 1: 采用 `log_manager` 原生方式，在调用点直接记录 `marker`
- Choice: 在每个 `DaiShanSQL` 调用点前后直接使用 `marker` 输出入参/出参日志，并复用现有 `trace` / `entry_trace` 调用链。
- Rationale: 与当前项目风格一致，最小改动即可接入；日志上下文与已有链路保持统一，降低认知成本。
- Alternative considered: 新增统一 wrapper 抽象层。缺点是引入额外间接层，偏离当前代码习惯，调试时跳转成本更高。

### Decision 2: 使用结构化字段输出，终端可读优先
- Choice: 日志字段最少包含 `call_site`、`method`、`args_preview`、`result_preview`、`duration_ms`、`success`、`error`。
- Rationale: 便于按字段检索和人工排障，同时控制日志体积。
- Alternative considered: 输出完整原始对象。缺点是过大、可读性差，并可能带来敏感信息风险。

### Decision 3: 结果与参数采用“序列化 + 限长裁剪”策略
- Choice: 对 dict/list/str 统一转字符串后限长（例如 500~2000 字符，可配置），超出部分追加截断标记。
- Rationale: 在保留定位信息的同时避免终端刷屏。
- Alternative considered: 不截断。缺点是高频调用可能显著影响可读性与运行日志体量。

### Decision 4: 异常路径必须记录并保持原异常传播
- Choice: 在调用点 `except` 分支通过 `marker(..., level=\"ERROR\")` 记录入参摘要、异常类型和错误信息后 `raise` 原异常。
- Rationale: 不能因日志增强改变错误处理语义。
- Alternative considered: 吞异常并返回默认值。缺点是会破坏现有业务行为。

### Decision 5: 覆盖矩阵以模块为单位执行
- Choice: 明确覆盖如下调用点：
  - `chat_general_service.py`: `sqlFixed.sql_ChemicalCompanyInfo`、`sqlFixed.sql_SecuritySituation`、`server.get_sql_result`、`server.judgeQuery`
  - `source_dispath_srvice.py`: 两处 `server.QueryBySQL`
  - `fetch_table_structures.py`: `server.QueryBySQL`
- Rationale: 与需求“都覆盖”一致，避免只覆盖主路径。

## Risks / Trade-offs

- [Risk] 日志过多影响终端可读性 → Mitigation: 使用摘要字段与可配置截断长度。
- [Risk] 序列化失败导致日志异常 → Mitigation: 调用点日志前做安全序列化兜底 `repr()`，日志失败不影响业务调用。
- [Risk] 个别调用点遗漏 → Mitigation: 用关键字扫描 `Server`/`QueryBySQL`/`get_sql_result`/`judgeQuery` 建立覆盖检查清单。
- [Risk] 打印敏感字段 → Mitigation: 预留字段脱敏规则（例如 token/password 字段替换为 `***`）。

## Migration Plan

1. 基于 `log_manager` 约定定义统一日志字段（`method`、`call_site`、`args_preview`、`result_preview`、`duration_ms`、`success`）。
2. 按覆盖矩阵在调用点接入 `marker` 前后日志与异常日志。
3. 运行现有测试与新增测试，确认业务结果不变。
4. 在本地启动后通过终端验证入参/出参日志样式与字段完整性。

## Open Questions

- 截断阈值是否固定（如 1000）还是通过 `.env` 提供配置项。
- 是否需要将日志输出级别区分为 `INFO`（成功）和 `WARNING/ERROR`（异常）。
