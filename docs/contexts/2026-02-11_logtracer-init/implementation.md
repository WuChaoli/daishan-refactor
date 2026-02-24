# LogTracer 实施记录

## 日期

- 2026-02-11

## 本轮目标

- 完成 M2 进阶：真实 OpenTelemetry + OTLP 导出 + Jaeger 接入基础能力

## 已完成改动

### 1. 依赖与环境

- 新增依赖（项目清单）：
  - `opentelemetry-api>=1.27.0`
  - `opentelemetry-sdk>=1.27.0`
  - `opentelemetry-exporter-otlp>=1.27.0`
- 更新文件：
  - `pyproject.toml`
  - `requirements.txt`

### 2. 配置系统扩展

- 在 `LogTracerConfig` 中新增：
  - `otlp_endpoint`
  - `otlp_insecure`
- 支持环境变量覆盖：
  - `LOGTRACER_OTLP_ENDPOINT`
  - `LOGTRACER_OTLP_INSECURE`

### 3. OTel 追踪模块

- 新增 `src/LogTracer/src/logtracer/tracing.py`
  - `configure_tracer(config, span_exporter=None, use_batch=True)`
  - `get_tracer(name)`
  - `get_tracer_provider()`
- 关键实现：
  - `TracerProvider` + `Resource(service.name)`
  - `ParentBased(TraceIdRatioBased)` 采样策略
  - `OTLPSpanExporter` 默认导出器

### 4. 装饰器升级

- `@trace_span` 改为使用真实 OTel span
- span 上下文同步写入 `logtracer.context`，保持日志事件与 trace 关联
- 保持 `@trace_io` 的 enter/exit/error 事件行为

### 5. 测试与文档

- 新增 OTel 集成测试：
  - `src/LogTracer/test/test_otel_tracing.py`
  - `src/LogTracer/test/test_jaeger_config.py`
- 更新 `src/LogTracer/README.md`：加入 OTel/Jaeger 使用说明

### 6. 无服务文件导出模式（新增）

- 新增配置项：
  - `export_mode`（`otlp` / `file`）
  - `trace_file_path`（默认 `src/LogTracer/logs/traces/traces.jsonl`）
- 新增 `JsonlSpanExporter`：
  - 文件：`src/LogTracer/src/logtracer/file_exporter.py`
  - 能力：span 以 JSONL 逐行落盘
- 新增回放能力：
  - 模块：`src/LogTracer/src/logtracer/replay.py`
  - 脚本：`src/LogTracer/scripts/replay_traces.py`
  - 视图：调用树（tree）+ 时序列表（timeline）

### 7. 新增测试

- `src/LogTracer/test/test_file_exporter.py`
- `src/LogTracer/test/test_replay_script.py`
- `src/LogTracer/test/test_jaeger_connection_check.py`

### 8. 演示样本生成能力（新增）

- 新增模块：`src/LogTracer/src/logtracer/sample_trace.py`
  - `generate_sample_trace_file(output_file, depth, breadth)`
  - `sample_cli_main(argv)`
- 新增脚本：`src/LogTracer/scripts/generate_sample_trace.py`
- 支持生成中样本（`depth=4, breadth=3`）40 个 span
- 默认可覆盖 `src/LogTracer/logs/traces/traces.jsonl`

### 9. 配置新增

- `export_mode`: `otlp` / `file`
- `trace_file_path`: 文件导出模式的 jsonl 路径

## 说明

- 本轮保持“独立项目”原则，未修改旧 `src/log_decorator` 代码。
