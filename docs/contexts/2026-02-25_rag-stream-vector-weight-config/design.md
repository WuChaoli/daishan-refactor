# 设计文档

## 设计目标

在不改变现有调用链结构的前提下，引入 `vector_similarity_weight` 的分层配置能力，并保持向后兼容。

## 设计方案

1. 配置模型扩展
   - `RAGFlowConfig` 新增 `vector_similarity_weight`（基础配置，默认 `0.3`）。
   - `IntentConfig` 新增可选 `vector_similarity_weight`（默认 `None`，表示继承）。
2. 生效规则
   - 若 `intent.vector_similarity_weight` 非空，则使用 intent 值。
   - 否则使用 `ragflow.vector_similarity_weight`。
3. 请求构造
   - `RagflowClient._query_with_sdk` 构造 `RetrievalRequest` 时传入生效权重。
4. 配置文件
   - 在 `ragflow` 节点设置 `vector_similarity_weight: 0.7`。
   - `intent` 节点保留注释形式的可选覆盖项说明。

## 测试策略

1. 单元测试验证继承场景（intent 未设置）。
2. 单元测试验证覆盖场景（intent 显式设置）。
3. 边界测试验证取值范围校验（0~1）。
4. 真实环境调用验证请求可成功执行。
