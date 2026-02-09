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

