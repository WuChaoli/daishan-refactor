# 实施记录

## 变更清单

1. 补全检索请求模型字段：
   - `src/ragflow_sdk/models/chunks.py`
2. 检索请求发送时剔除空值字段：
   - `src/ragflow_sdk/core/client.py`
3. 新增测试归档：
   - `test/2026-02-25_ragflow-sdk-retrieval-params/test_retrieval_request_params.py`
4. 更新测试归档索引：
   - `test/README.md`
5. 新增上下文文档并登记索引：
   - `docs/contexts/2026-02-25_ragflow-sdk-retrieval-params/`
   - `docs/contexts/.contexts-index.json`

## 实施说明

1. 在 `RetrievalRequest` 中新增 RAGFlow 检索接口缺失参数。
2. 增加模型级校验，保证 `dataset_ids` 与 `document_ids` 至少一个存在。
3. `retrieve` 发送请求时使用 `exclude_none=True`，避免把可选字段以 `null` 发给服务端。
4. 通过单元测试验证新增字段序列化、参数校验与请求发送行为。
