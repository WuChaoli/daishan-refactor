# Phase 06: 分类驱动检索 - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning

<domain>
## Phase Boundary

将 Phase 5 实现的 IntentClassifier 与现有向量检索流程连接，实现两阶段识别机制：

1. **粗分类**：LLM 判断问题类型（岱山-指令集 1 / 岱山-数据库问题 2 / 岱山-指令集-固定问题 3）
2. **精检索**：仅在对应类型的向量库中检索具体问题
3. **跨库隔离**：不同意图类型的查询不会跨库混淆检索结果

核心策略：置信度 >= 0.7 时信任分类结果并过滤检索范围，< 0.7 时走全量检索保持向后兼容。
</domain>

<decisions>
## Implementation Decisions

### 分类调用策略
- **调用时机**：检索前调用分类，不存储在会话中（每次重新分类）
- **置信度决策**：>= 0.7 时应用分类结果（过滤 database_mapping），< 0.7 时全量检索
- **降级处理**：degraded=True 或置信度 < 0.7 时走现有全量检索流程

### 置信度阈值配置
- 在 `config.yaml` 的 `intent_classification` 配置块中添加 `confidence_threshold` 字段
- 默认值 0.7，允许运行时调整
- 复用 Phase 5 的 IntentClassificationConfig 模型扩展该字段

### 数据库映射策略
- **复用现有机制**：使用 BaseIntentService 和 IntentService 现有的 `database_mapping`
- 不硬编码 type_id 到 database_name 的映射
- 高置信度时通过过滤 `database_mapping` 只查询对应类型的库

### 降级标记策略
- **添加降级 marker**：专门的 `classifier.degraded_fallback` 标记
- 记录低置信度（< 0.7）和降级（degraded=True）时的 fallback 行为
- 便于观测降级频率和诊断问题

### 输出格式保持
- **保持现有格式**：不添加显式标记字段
- 通过 `database` 和 `results` 列表隐含分类结果
- 低置信度时隐式表示（无需 classification_used 字段）

### Claude's Discretion
- `database_mapping` 中 type_id 到 database_name 的映射定义方式（配置文件或代码注释）
- RagflowClient 是否需要扩展支持按 type_id 过滤的参数，或由调用方过滤
</decisions>

<specifics>
## Specific Ideas

- "混合返回"策略确保低置信度时仍能返回结果，同时高置信度时避免跨库混淆
- 置信度阈值 0.7 是经验值，允许通过配置调优
- 降级 marker 便于生产环境监控分类器表现
</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- **IntentClassifier** (`src/rag_stream/src/utils/intent_classifier.py`)：已实现 LLM 分类，支持降级、超时、验证
- **IntentService** (`src/rag_stream/src/services/intent_service/intent_service.py`)：意图识别服务主类，已集成 IntentClassifier
- **BaseIntentService** (`src/rag_stream/src/services/intent_service/base_intent_service.py`)：模板方法流程，`_query_table_results` 当前全量查询
- **RagflowClient**：向量检索客户端，负责与 RAGFlow API 交互

### Established Patterns
- **模板方法模式**：BaseIntentService 定义 `_query_process_table_results` → `_sort_process_table_results` → `_post_process_result` 流程
- **配置加载模式**：通过 YAML + 环境变量覆盖（Phase 5 已实现）
- **Marker 日志**：使用 `log-manager` 进行结构化事件追踪
- **降级兜底**：异常时返回安全默认值，保持服务可用性

### Integration Points
- **IntentService._load_process_settings**（第 107-118 行）：预留分类器调用位置，需在此处调用 `classify()`
- **BaseIntentService._query_table_results**（第 341-372 行）：当前查询所有映射表，需根据置信度过滤 `database_mapping.keys()`
- **config.yaml**：需添加 `intent_classification.confidence_threshold` 配置项
</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope
</deferred>

---
*Phase: 06-分类驱动检索*
*Context gathered: 2026-02-28*
