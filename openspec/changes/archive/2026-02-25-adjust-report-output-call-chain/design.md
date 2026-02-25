## Context

当前实现位于 `src/log-manager/log_manager/reporting.py`，入口报告由 `lines: list[str]` 逐行拼接中文段落后写入 `latest.txt`。调用链已可重建（基于 `SpanNode` 树和 `_append_tree`），但输出是面向人阅读的纯文本结构，难以被下游程序稳定解析，也无法对“函数名、耗时、异常”做字段级处理。

本次变更目标是将入口报告内容替换为 YAML 结构，保留现有报告落盘路径和触发机制。用户已明确要求使用 YAML，并以“函数名、耗时、异常”为核心字段。

## Goals / Non-Goals

**Goals:**
- 将入口报告内容从纯文本替换为 YAML 文档。
- 在 `call_chain` 中输出层级化节点，且每个节点包含 `function_name`、`duration_ms`、`exception`。
- 保留现有报告生成时机、目录结构和文件命名策略，避免影响运行时触发流程。
- 让测试从字符串包含判断升级为 YAML 结构断言。

**Non-Goals:**
- 不重构事件采集链路（`runtime` / `decorators` / `storage`）。
- 不新增新的报告触发类型或调度机制。
- 不在本次变更中扩展额外复杂字段（如参数快照、返回值快照）。

## Decisions

### Decision 1: 报告生成改为“先组装结构，再序列化 YAML”
- 方案 A（采用）：新增内部结构化组装逻辑（如 `_build_entry_report_payload`），返回 `dict`，最终用 `yaml.safe_dump(..., allow_unicode=True, sort_keys=False)` 输出。
- 方案 B（不采用）：继续生成纯文本并追加 YAML 片段。
- 取舍：A 能保证结构一致和可测试性；B 会形成双格式混合，难以维护。

### Decision 2: 调用链节点字段最小化，严格满足需求
- 节点统一结构：`function_name`、`duration_ms`、`exception`、`children`。
- `exception` 语义：无异常时为 `null`；有异常时为 `{type, message}`。
- 方案对比：
  - 方案 A（采用）：固定最小字段集合，先满足核心场景。
  - 方案 B（不采用）：一次性加入参数/返回值/内存等更多字段。
- 取舍：A 变更面可控，避免对上游事件字段依赖过深。

### Decision 3: 执行“替换”而非“兼容双轨”
- 方案 A（采用）：入口报告完全替换为 YAML 内容，不再输出 `【函数调用链】` 等旧标题文本。
- 方案 B（不采用）：增加配置开关支持新旧格式并存。
- 取舍：用户已明确“替换”；双轨会增加长期维护成本与测试矩阵。

### Decision 4: 文件路径保持不变
- 继续写入 `reports/<session>/entries/<entry_id>/report-*.txt` 与 `latest.txt`，仅替换内容格式。
- 这样可避免对 `storage` 路径约定和轮转逻辑产生额外改动。

## Risks / Trade-offs

- [风险] 下游若依赖旧文本标题或固定行文，会出现解析失败。  
  → Mitigation：同步更新相关测试与文档，明确入口报告现为 YAML。

- [风险] YAML 序列化中 `None/数字/中文` 表现与预期不一致。  
  → Mitigation：统一使用 `yaml.safe_dump` 参数并增加结构化断言测试。

- [风险] 调用链树深度较深时，YAML 可读性下降。  
  → Mitigation：保持缩进默认策略，后续如需可引入可视化导出（非本次范围）。

## Migration Plan

1. 在 `reporting.py` 中引入 YAML 序列化依赖，新增入口报告 payload 构建逻辑。
2. 将当前文本拼接（含旧标题段）替换为 YAML payload 输出。
3. 调整 `src/log-manager/tests/test_reporting.py`：从文本包含断言改为 YAML 结构断言。
4. 更新 `src/log-manager/docs/operations.md` 与必要使用说明，声明入口报告内容为 YAML。
5. 回归验证：报告触发链路、文件落盘与保留策略不回退。

回滚策略：若线上/本地集成方受影响，可回滚到上一个提交恢复旧文本输出（本次不引入运行期开关）。

## Open Questions

- 全局汇总报告（`global-error-summary/latest.txt`）是否也应在后续统一迁移为 YAML？
