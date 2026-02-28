# Phase 5: 意图分类基础 - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning

## Phase Boundary

本阶段在现有意图识别流程中引入粗粒度分类层，将意图识别分为两个阶段：粗分类（LLM）→ 精检索（向量库）。

## Implementation Decisions

### 分类服务设计

**Decision: 在 BaseIntentService 基类中新增分类模板方法，子类可选重写**
**Rationale:** 保持现有架构模式，BaseIntentService 已定义完整的识别流程模板，子类只需补充分类逻辑
**Code Context:** `BaseIntentService._build_process_error_result()` 返回统一格式，`_sort_process_table_results()` 支持排序扩展
**Outcome:** 待实现后验证

### 分类 Prompt

**Decision: 使用结构化 prompt，要求 LLM 返回 JSON Schema（0/1/2/3）**
**Rationale:** 结构化输出比自然语言更可靠，便于解析和验证；可参考 intent_mapping.example.json 中的类型定义
**Example Prompt:**
```
你是问题分类助手。请根据用户的问题，判断其属于以下哪种类型：

0 - 岱山-指令集
1 - 岱山-数据库问题
2 - 岱山-指令集-固定问题

只返回类型对应的数字编号（0/1/2/3），不要添加其他说明。

输入：{user_query}
输出：{"type": 数字编号}
```
**Outcome:** 待实现后测试验证

### 分类结果格式

**Decision: 返回整数 ID（1/2/3），保持现有数字逻辑**
**Rationale:** 与现有 intent_mapping.example.json 中的映射关系一致，便于检索时直接使用；整数 ID 便于下游处理和日志记录
**Code Context:** `IntentRecognizerSettings` 中的 `database_mapping` 使用字符串键名，值为类型 ID
**Outcome:** 与现有系统兼容

### 降级策略

**Decision: 分类失败、超时或返回未知类型时，降级到现有向量检索流程**
**Rationale:** 确保服务可用性，分类服务不可用时不应阻断主流程；超时设置 3 秒，失败后立即降级（不重试）
**Code Context:** 参考 `BaseIntentService._build_process_error_result()` 的错误返回模式
**Outcome:** 降级路径已明确

### 超时与重试

**Decision: 超时设置 3 秒，失败后立即降级（不重试）**
**Rationale:** 快速失败可提升用户体验，避免长时间等待；重试增加复杂度，本次采用快速降级策略
**Code Context:** 可配置 `intent_classification.timeout` 参数，传递给 QueryChat
**Outcome:** 响应时间可控

### 配置管理

**Decision: 复用现有 intent_mapping.example.json 格式（database_mapping）**
**Rationale:** 避免引入新的配置格式，保持配置一致性；现有工具链已支持该格式
**Code Context:** `IntentRecognizerSettings` 从 JSON 加载，包含 `similarity_threshold`, `top_k`, `default_type`, `database_mapping`
**Outcome:** 配置管理逻辑可复用

### 日志与监控

**Decision: 复用现有 marker/trace 机制**
**Rationale:** 保持日志格式统一，便于追踪和调试；不需要新增专门的分类标记
**Code Context:** 使用 `marker("intent_classification", {...})` 记录分类结果
**Outcome:** 日志链一致

## Existing Code Insights

### Reusable Assets

- `QueryChat` 工具类（`src/rag_stream/src/utils/query_chat.py`）- v1.0 已实现，支持异步调用、内容验证、统计指标
- 配置加载机制（`src/rag_stream/src/config/settings.py`）- 支持 JSON 文件和环境变量覆盖
- 日志标记系统（`src/utils/log_manager_import`）- 统一的事件追踪机制

### Established Patterns

- 异步服务模式：使用 `asyncio` 处理并发请求，核心业务逻辑使用 `asyncio.to_thread` 包装同步调用
- 模板方法模式：`BaseIntentService` 定义抽象模板方法，子类实现具体逻辑
- 配置驱动设计：通过 JSON 配置文件驱动行为，便于运维和调优
- 降级兜底模式：异常时返回安全默认值，保持服务可用性

### Integration Points

- 新分类服务将连接到：`IntentService._load_process_settings()` 和 `_query_process_table_results()`
- 分类结果需要传递给：`BaseIntentService._build_intent_result_from_table_results()`
- 配置文件路径：需要适配 `intent_mapping.example.json` 格式或新增 `intent_classification.json`

## Specific Ideas

- 分类 prompt 的 system message 可以包含类型定义和示例问题，提升准确度
- 考虑在配置中添加 classification_enabled 开关，便于调试和灰度发布
- 分类服务的入口可以与 `handle_chat_general` 对齐，返回 `IntentRecognitionResult` 格式
