# 实施记录

## 变更清单

1. 配置模型扩展：
   - `src/rag_stream/src/config/settings.py`
2. 检索调用权重接入：
   - `src/rag_stream/src/utils/ragflow_client.py`
3. 配置文件新增参数：
   - `src/rag_stream/config.yaml`
4. 单元测试新增：
   - `test/2026-02-25_rag-stream-vector-weight-config/test_vector_similarity_weight_config.py`
5. 文档与索引更新：
   - `docs/contexts/2026-02-25_rag-stream-vector-weight-config/`
   - `docs/contexts/.contexts-index.json`
   - `test/README.md`

## 实施说明

1. 在 `RAGFlowConfig` 中新增基础向量权重参数，并做区间校验。
2. 在 `IntentConfig` 中新增可选覆盖参数，并保留继承语义。
3. 在 `RagflowClient` 内部增加“生效权重”解析函数，并用于 `RetrievalRequest`。
4. 通过测试验证继承/覆盖逻辑和参数校验。
5. 通过真实环境调用验证改动可用。
