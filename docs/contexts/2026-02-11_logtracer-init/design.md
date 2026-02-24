# LogTracer 设计文档

## 1. 设计目标

LogTracer 采用“调用链追踪 + 结构化 I/O 日志”双轨方案，核心目标：

- 用 Trace 准确展示函数调用路径与耗时
- 用结构化日志展示函数入参/出参摘要与运行状态
- 用统一 `trace_id` 关联链路与日志，提升排障效率

## 2. 总体架构

```text
Application Code
  └─ @trace_io / @trace_span
      ├─ Tracing Layer (OpenTelemetry)
      │   ├─ span create/end
      │   ├─ parent-child context propagation
      │   └─ OTLP exporter
      └─ Logging Layer (JSON)
          ├─ event: enter/exit/error
          ├─ args/result summary
          └─ masking + truncation

Storage/Viewer
  ├─ Jaeger (trace visualization)
  └─ local log files (worker-isolated)
```

## 3. 模块划分

- `core/config/`
  - 配置加载与校验（`.env > yaml > json`）
- `core/tracing/`
  - OTel 初始化、provider、exporter、采样器
- `core/decorators/`
  - `@trace_span` 与 `@trace_io`（sync/async）
- `core/logging/`
  - JSON logger、worker 日志文件命名、字段规范
- `core/sanitize/`
  - 脱敏规则、截断策略、摘要序列化
- `core/errors/`
  - 异常分类、错误事件构建、错误链采集

## 4. 关键设计点

### 4.1 调用链追踪

- 以函数调用为 span 粒度
- span 名称规范：`<module>.<function>`
- 默认记录：`trace_id`、`span_id`、`parent_span_id`、`duration_ms`、`status`
- 异常时写 `record_exception` 并置 `status=ERROR`

### 4.2 入参/出参日志

- 事件模型：
  - `enter`（函数开始）
  - `exit`（函数返回）
  - `error`（函数异常）
- 仅记录摘要，避免大对象与敏感信息泄露
- 支持按字段白名单/黑名单控制

### 4.3 异步与并发稳定性

- 基于 OpenTelemetry context 管理 parent-child
- 不依赖树形文本缩进推导调用关系
- 并发下通过 `trace_id` 精确定位同一请求

### 4.4 多 worker 日志隔离

- 文件命名：`global.{pid}.log`、`error.{pid}.log`
- 每条日志携带 `pid`、`worker_id`、`trace_id`

## 5. 配置模型

优先级：

1. `.env`
2. `config.yaml`
3. `config.json`

关键配置项：

- `service_name`
- `otlp_endpoint`
- `sampling_ratio`
- `log_level`
- `args_max_len` / `result_max_len`
- `mask_rules`
- `worker_log_isolation`

## 6. 验收设计

- 功能验收：
  - Jaeger 可看到完整调用链
  - I/O 日志可按 `trace_id` 关联
  - 敏感字段默认脱敏
- 稳定性验收：
  - 异步并发下无调用层级错乱
  - 多 worker 下日志无串线
- 质量验收：
  - 核心模块覆盖率达到 80%+

