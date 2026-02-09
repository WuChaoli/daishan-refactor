---
name: log-decorator
description: 面向本项目 log_decorator 模块的接入、参数设计、日志排障与调用链分析指南。用于新增或修改 @log 装饰器、设计 args_handler 或 result_handler、排查 logs/global.log 与 logs/error.log、分析 logs/mermaid 产物、处理日志级别与脱敏规则异常；当用户提到“log_decorator”“函数日志装饰器”“调用链日志”“Mermaid 调用图”“入口函数日志”“敏感字段脱敏”时使用。
---

# Log Decorator

在本项目中为函数调用提供统一日志、入口链路追踪和 Mermaid 调用图输出。
优先使用本技能快速完成接入、参数选型、日志验证与故障定位。

## 执行流程

### 1) 读取基线与目标

- 先读取 `src/log_decorator/README.md`，确认当前实现行为。
- 明确任务类型：
  - 新增函数日志接入
  - 调整 `@log(...)` 参数
  - 排查日志或 Mermaid 未按预期生成
  - 处理敏感字段脱敏或日志级别问题

### 2) 选择最小参数方案

- 仅在需要时开启功能：
  - 默认记录：`print_args=True`、`print_result=True`、`print_duration=True`
  - 入口链路：仅在入口函数设置 `is_entry=True`
  - Mermaid：设置 `enable_mermaid=True`；需要稳定落盘时加 `force_mermaid=True`
  - 高并发或高频函数：按需关闭 `print_args` 或 `print_result`
- 优先使用 `references/log-decorator-playbook.md` 的参数速查与模板。

### 3) 处理入参与出参可读性

- 需要业务可读日志时，实现 `args_handler(args, kwargs)` 和 `result_handler(result)`。
- 保持 handler 幂等、轻量、无副作用，避免阻塞业务。
- handler 抛错时允许降级，不影响业务函数返回。

### 4) 验证日志与产物

- 验证全局日志：`logs/global.log`。
- 若入口函数启用，验证入口日志：`logs/{entry_func}.log`。
- 入口异常时，验证增强错误日志：`logs/error.log`。
- 启用 Mermaid 时，验证 `logs/mermaid/{entry_func}/` 是否生成 `.md` 文件。

### 5) 定位常见问题

- Mermaid 未生成时，按顺序检查：
  1. 是否为入口函数 `is_entry=True`
  2. 是否启用 `enable_mermaid=True`
  3. 是否满足触发条件之一（`force_mermaid=True`、有效级别 `DEBUG`、入口链路异常）
- 日志级别异常时，检查 `log_level` 是否为有效级别或可执行 lambda。
- 参数泄露风险时，优先自定义 `args_handler`，并确认脱敏规则覆盖字段。

## 产出要求

- 给出具体改动文件与改动理由。
- 给出最小验证命令与结果。
- 若行为不符预期，给出根因、修复点和回归验证。

## 参考资料

- 关键规则与参数速查：`references/log-decorator-playbook.md`
- 源实现与完整说明：`src/log_decorator/README.md`

## 交付检查清单

- [ ] `SKILL.md` frontmatter 仅包含 `name` 与 `description`
- [ ] `description` 明确“做什么 + 何时使用 + 触发词”
- [ ] 提供最小实施流程与排障步骤
- [ ] 参考资料与代码实现路径可直接定位
