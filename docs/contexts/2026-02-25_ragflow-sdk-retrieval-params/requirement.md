# 需求文档

## 背景

当前 `src/ragflow_sdk/models/chunks.py` 的 `RetrievalRequest` 参数不完整，缺少 RAGFlow 检索接口文档中的多个请求字段。

## 需求说明

1. 基于 `/api/v1/retrieval` 文档补全 `RetrievalRequest` 请求参数。
2. 仅修改 SDK 侧（`src/ragflow_sdk/`），不改业务调用层。
3. 保持向后兼容：现有调用不因新增字段而失败。
4. 支持通过 `document_ids` 发起检索请求。

## 验收标准

1. `RetrievalRequest` 包含新增参数字段，并可正确序列化到请求体。
2. `dataset_ids` 与 `document_ids` 至少提供一个。
3. 新增单元测试覆盖新增字段和校验行为。
