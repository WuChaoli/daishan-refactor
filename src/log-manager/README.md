# log-manager

Python 本地运行时观测工具，目标是低侵入记录、增量分析和中文报告输出。

## 核心能力

- 双装饰器模型：
  - `@entry_trace`：入口级独立日志与报告
  - `@trace`：函数级调用追踪（无入口时自动写入全局流）
- 结构化事件：
  - `call_enter` / `call_exit` / `error` / `marker` / `process_mem`
- 增量报告：
  - 定时触发、事件阈值触发、空闲触发、严重错误立即触发
- 输出契约：
  - 终端格式：`[时间] [等级] [函数名] 提示文本`
  - 完整报告只写文件（入口报告 + 全局错误汇总）

## 安装

```bash
pip install -e .
```

开发依赖（pytest）：

```bash
pip install -e ".[dev]"
```

## 快速开始

```python
from pathlib import Path
from log_manager import LogManagerConfig, configure, entry_trace, trace, marker

cfg = LogManagerConfig(enable_background_threads=False)
cfg.base_dir = Path(".log-manager")
cfg.session_id = "sess_demo"
cfg.parameter_whitelist = ("order_id", "sku")
runtime = configure(cfg)

@trace
def reserve(order_id: str, sku: str):
    marker("库存检查开始", {"order_id": order_id, "sku": sku})
    raise RuntimeError("inventory timeout")

@entry_trace("create-order")
def create_order(order_id: str):
    reserve(order_id=order_id, sku="sku-77")

try:
    create_order("o_1001")
except RuntimeError:
    pass

runtime.flush_reports(reason="manual")
runtime.shutdown()
```

## 目录与输出

- 包代码：
  - `log_manager/`
- 测试：
  - `tests/`
- 文档：
  - `docs/usage.md`
  - `docs/operations.md`
  - `docs/validation.md`

默认输出目录（`base_dir=.log-manager`）：

- 事件：
  - `runs/<session>/entries/<entry_id>.events.jsonl`
  - `runs/<session>/global.events.jsonl`
- 报告：
  - `reports/<session>/entries/<entry_id>/latest.txt`
  - `reports/<session>/global-error-summary/latest.txt`

## 主要配置项

- `mode`: `lite` / `enhanced`
- `session_id`: 可选，显式指定会话 ID（多进程共享会话时建议设置）
- `memory.process_enabled`
- `memory.span_enabled`
- `memory.sampling_interval_ms`
- `report.trigger_timer_s`
- `report.trigger_event_count`
- `report.trigger_idle_s`
- `report.immediate_on_error`
- `report.retention`
- `console.show_memory_delta`

## 测试

执行测试：

```bash
python -m pytest -q
```

如果环境没有 pytest，先安装开发依赖（见“安装”）。
