## 1. Report YAML 化改造

- [x] 1.1 在 `src/log-manager/log_manager/reporting.py` 中新增入口报告 payload 组装逻辑（metadata/error_summary/call_chain/error_path/chain_memory_top）
- [x] 1.2 将入口报告输出从逐行文本拼接替换为 `yaml.safe_dump` 序列化输出，并保持现有报告目录与文件命名不变
- [x] 1.3 实现调用链节点序列化：每个节点输出 `function_name`、`duration_ms`、`exception`，并在有子调用时输出 `children`
- [x] 1.4 移除入口报告中旧的纯文本标题段（如 `【函数调用链】`、`【错误路径链】`）以满足“替换输出”要求

## 2. 测试与回归

- [x] 2.1 更新 `src/log-manager/tests/test_reporting.py`：将文本包含断言改为 YAML 解析后的结构断言
- [x] 2.2 新增/补充测试：无异常节点 `exception: null`，异常节点包含 `exception.type` 与 `exception.message`
- [x] 2.3 新增/补充回归断言：新报告内容不再包含旧文本标题标记
- [x] 2.4 执行 `src/log-manager/tests` 下与 reporting 相关测试并修复失败项

## 3. 文档同步与验收

- [x] 3.1 更新 `src/log-manager/docs/operations.md`，声明入口报告内容格式已切换为 YAML
- [x] 3.2 更新必要使用说明（如 `src/log-manager/docs/validation.md`）以匹配新报告结构
- [x] 3.3 验证一次完整报告生成流程，确认调用链字段满足 `function_name`/`duration_ms`/`exception`
