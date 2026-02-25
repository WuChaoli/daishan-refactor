# 测试归档索引

## 2026-02-25

- `2026-02-25_rag-stream-vector-weight-config`
  - 目标：将 `vector_similarity_weight` 配置化（ragflow 基础 + intent 可选覆盖）并验证检索请求传参
  - 类型：单元测试 + 真实环境联调
  - 执行命令：`PYTHONPATH=src/rag_stream:src ./.venv/bin/pytest -q test/2026-02-25_rag-stream-vector-weight-config/test_vector_similarity_weight_config.py`

- `2026-02-25_ragflow-sdk-retrieval-params`
  - 目标：补全 `RetrievalRequest` 的 RAGFlow 检索参数并验证序列化/参数校验
  - 类型：单元测试
  - 执行命令：`PYTHONPATH=. ./.venv/bin/pytest -q test/2026-02-25_ragflow-sdk-retrieval-params/test_retrieval_request_params.py`

## 2026-02-24

- `2026-02-24_intent-service-type3-integration`
  - 目标：验证一批园区问句在 `IntentService.process_query` 下返回意图类型 `3`
  - 类型：集成测试（真实 RagflowClient 链路）
  - 执行开关：`RUN_RAGFLOW_INTENT_INTEGRATION=1`
