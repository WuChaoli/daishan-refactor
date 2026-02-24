# log_decorator 更新日志

## 2026-02-09

### docs: 同步 README 与当前实现

本次文档更新基于 `log_decorator` 当前代码行为，重点修正与补充：

- 重写 `README.md`，移除重复章节与过时示例
- 同步 `@log()` 最新参数：`args_handler`、`force_mermaid`、`log_level`
- 明确 Mermaid 触发条件（`DEBUG` / 异常 / `force_mermaid`）
- 明确 Mermaid 当前输出为 `.md` 文件（包含 ASCII 树 + 性能表 + Mermaid 图）
- 补充错误增强日志 `logs/error.log` 结构（调用链、异常链、脱敏入参、Mermaid 链接）
- 补充敏感字段脱敏规则（`api_key`、`password`、`token`、`secret`、`key`）
- 同步 `parse_obj` 的紧凑模式与完整模式行为说明
- 同步配置优先级与配置项说明，并标注 `mermaid_enabled` 当前未参与装饰器启停判断

## 2026-02-11

### feat: 新增 `@log_entry` / `@log_end`，废弃 `is_entry`

- 新增 `@log_entry(...)`：替代 `@log(is_entry=True)` 作为调用链入口装饰器
- 新增 `@log_end(...)`：用于截止当前嵌套分支，后续 `@log(...)` 从新分支继续
- `@log()` 移除 `is_entry` 参数，传入时将触发参数错误
- 全量迁移项目内 `@log(is_entry=True)` 到 `@log_entry(...)`
- 更新 `README.md`：新增迁移指南与 `@log_end(...)` 使用说明

### docs: 精简 README 与技能文档对齐

- 精简 `README.md` 结构：新增“装饰器说明”并明确 `log/log_entry/log_end` 分工
- 明确 `@log_end(...)` 语义：截止当前分支，外层继续，下游按新分支记录
- 精简迁移示例，聚焦 `is_entry -> @log_entry` 的最小替换路径
- 同步更新 `log-decorator` 技能文档，移除过时的 `is_entry` 指引

### feat: 新增日志图标体系（函数头/分组/告警）

- 函数头新增 emoji 标识：`🔵 @log`、`🟢 @log_entry`、`🟣 @log_end`
- 入参与出参分组图标调整为：`🧩 [ args ]`、`🧪 [ returns ]`
- warning/error 形状区分：`⚠`（warning）、`✖`（error）
- 运行日志正文保持原样，不增加额外图标
- 同步更新相关测试断言与 README 示例

### feat: 图标主题配置化 + 全异常写入 error.log

- 新增 `icon_theme` 与 `icon_themes` 配置（仅作用于函数头与分组）
- 预置 `default` 与 `minimal` 两套主题，支持切换
- `@log/@log_entry/@log_end` 任意异常都会写入 `logs/error.log`
- `error.log` 新增 `错误摘要` 与 `错误位置` 字段，便于快速定位问题
- 同步更新 README 配置说明与测试用例

### feat: 入口日志目录收敛与命名规范化

- `@log_entry` 日志不再写入 `logs/` 根目录
- 统一写入 `logs/entries/` 子目录
- 命名规则改为 `{module_file}.{entry_func}.log`
- 不迁移历史根目录日志文件，仅影响新写入
