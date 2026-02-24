---
name: log-decorator
description: 面向本项目 log_decorator 模块的接入、参数设计、日志排障与调用链分析指南。用于新增或修改 @log/@log_entry/@log_end 装饰器、设计 args_handler 或 result_handler、排查 logs/global.log 与 logs/error.log、分析 logs/mermaid 产物、处理日志级别/树状对齐/敏感字段脱敏异常；当用户提到“log_decorator”“函数日志装饰器”“调用链日志”“Mermaid 调用图”“入口函数日志”“敏感字段脱敏”“logging.DEBUF”时使用。
---

# Log Decorator

用于快速完成 `log_decorator` 的接入、调参与排障。
先对齐当前实现，再做最小变更并验证。

## 当前基线（2026-02）

- 默认参数：`@log(print_args=True, print_result=True, print_duration=False)`。
- 入口函数使用 `@log_entry(...)`，不再使用 `is_entry` 参数。
- 边界截止使用 `@log_end(...)`：截止当前分支，外层可继续，下游默认新分支。
- 树状样式：`├─ / │ / └─`，入参分组 `🟦 [ args ]`，出参分组 `🟦 [ returns ]`。
- 运行时日志：`from log_decorator import logging`，支持 `logging.DEBUF/INFO/WARNING/ERROR`。
- 多行日志续行对齐依赖 `AlignedMultilineFormatter` 与 `%(levelname)-7s`。

## 快速决策

1. 普通函数日志：使用 `@log(...)`。
2. 请求/任务入口：使用 `@log_entry(...)`。
3. 流程边界清理：使用 `@log_end(...)`。
4. 仅在需要时开启 `enable_mermaid` / `force_mermaid`。
5. 高频路径按需关闭 `print_args` 或 `print_result`。

## 执行步骤

### 1) 对齐实现

- 先读 `src/log_decorator/README.md` 与 `src/log_decorator/decorator.py`。
- 确认是否涉及：参数变化、日志样式、Mermaid、错误增强、脱敏。

### 2) 最小实现

- 优先复用现有参数与工具函数，避免新增抽象。
- 需要业务可读性时才加 `args_handler` / `result_handler`。
- 处理 handler 异常时必须降级，不能影响业务返回。

### 3) 验证产物

- `logs/global.log`：基本日志是否正确。
- `logs/{entry_func}.log`：入口日志是否落盘。
- `logs/error.log`：异常链、调用链、脱敏、Mermaid 路径。
- `logs/mermaid/{entry_func}/`：是否生成 `.md` 文件。

### 4) 常见排障

- Mermaid 未生成：检查 `@log_entry(enable_mermaid=True)` 与触发条件（`force_mermaid` / DEBUG / 异常）。
- 树状错位：检查 formatter 与日志格式是否匹配。
- 日志级别异常：检查 `log_level` 是否有效或 lambda 是否抛错。
- 参数泄露风险：优先审查 `args_handler` 与脱敏规则覆盖面。

## 交付要求

- 说明改动文件与改动理由。
- 给出最小验证命令与结果。
- 若有未完成项，明确阻塞点与下一步。

## 参考

- `src/log_decorator/README.md`
- `src/log_decorator/decorator.py`
- `src/log_decorator/mermaid.py`
- `src/log_decorator/parser.py`
