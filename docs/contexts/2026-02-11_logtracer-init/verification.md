# LogTracer 验证记录

## 日期

- 2026-02-11

## 验证命令

```bash
./.venv/bin/pytest -q src/LogTracer/test
PYTHONPATH=src/LogTracer/src ./.venv/bin/python src/LogTracer/scripts/demo.py
PYTHONPATH=src/LogTracer/src ./.venv/bin/python src/LogTracer/scripts/check_jaeger_connection.py --endpoint http://127.0.0.1:4317
PYTHONPATH=src/LogTracer/src ./.venv/bin/python src/LogTracer/scripts/replay_traces.py --file src/LogTracer/logs/traces/traces.jsonl --view both
PYTHONPATH=src/LogTracer/src ./.venv/bin/python src/LogTracer/scripts/generate_sample_trace.py --output src/LogTracer/logs/traces/traces.jsonl --depth 4 --breadth 3
```

## 预期结果

- 所有 `src/LogTracer/test` 测试通过
- demo 输出 sync/async 返回值和事件列表
- 事件中包含非空 `trace_id` / `span_id`
- OTLP 检查脚本可按连通状态返回正确退出码
- 回放脚本可输出调用树与时序视图
- 样本生成脚本可输出中样本（40 spans）并可被回放脚本读取
- 回放脚本默认“写文件 + 打印终端”

## 实际结果

- `./.venv/bin/pytest -q src/LogTracer/test`
  - 结果：`23 passed in 0.22s`
- `PYTHONPATH=src/LogTracer/src ./.venv/bin/python src/LogTracer/scripts/demo.py`
  - 结果：
    - `sync_result=3`
    - `async_result=7`
    - 事件列表中 `trace_id/span_id` 均为非空
- `check_jaeger_connection.py`（提权）
  - 结果：`Connection refused`（说明端口无监听，脚本判定逻辑正确）
- `generate_sample_trace.py`
  - 结果：`Generated 40 spans into src/LogTracer/logs/traces/traces.jsonl`
- `replay_traces.py`（默认配置）
  - 结果：终端打印完整内容
  - 结果：`src/LogTracer/logs/traces/replay_output.txt` 被覆盖写入

## 风险与后续

- 当前仅完成 OTLP 导出与本地测试验证，Jaeger 端可视化需目标端服务可达。
- 下一步可补充：
  - 真实端到端 Jaeger 连通性脚本
  - span 属性标准化（业务 tags）
  - 异常分级与告警联动
