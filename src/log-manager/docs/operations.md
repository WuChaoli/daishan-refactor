# 运行模式与开销说明

## 模式

- `lite`（默认）：
  - 内存采样周期较长（默认 1000ms）
  - 适合常态运行与低侵入排障
- `enhanced`：
  - 内存采样周期更短（默认不高于 200ms）
  - 适合短时间深度诊断

## 关键开关

- `memory.process.enabled`：进程内存采样开关
- `memory.span.enabled`：函数进出内存差值开关
- `report.chain_memory.enabled`：报告调用链内存板块开关
- `console.show_memory_delta`：终端是否展示内存变化

## 报告与日志路径

- 事件日志：
  - `runs/<session>/entries/<entry_id>.events.jsonl`
  - `runs/<session>/global.events.jsonl`
- 报告：
  - `reports/<session>/entries/<entry_id>/latest.txt`
  - `reports/<session>/global-error-summary/latest.txt`

## 报告触发策略

- 定时触发：`T`
- 事件阈值触发：`N`
- 空闲触发：`I`
- 严重错误触发：立即生成快照
