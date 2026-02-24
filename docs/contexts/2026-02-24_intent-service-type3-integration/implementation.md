# 实施记录

## 变更清单

1. 新增集成测试文件：
   - `test/2026-02-24_intent-service-type3-integration/test_intent_service_type3_integration.py`
2. 新增测试归档索引：
   - `test/README.md`
3. 新增上下文文档：
   - `docs/contexts/2026-02-24_intent-service-type3-integration/requirement.md`
   - `docs/contexts/2026-02-24_intent-service-type3-integration/design.md`
   - `docs/contexts/2026-02-24_intent-service-type3-integration/implementation.md`

## 实施说明

1. 按用户给定样例构建 40 条参数化问句。
2. 固定期望值 `EXPECTED_INTENT_TYPE = 3`。
3. 使用真实 `RagflowClient` 与 `IntentService` 执行完整识别链路。
4. 通过环境变量开关控制外部依赖访问，默认不自动连接外部服务。

## 执行方式

```bash
RUN_RAGFLOW_INTENT_INTEGRATION=1 \
PYTHONPATH=src/rag_stream \
./.venv/bin/pytest -q test/2026-02-24_intent-service-type3-integration/test_intent_service_type3_integration.py
```

## 备注

- 若网络或 RAGFlow 服务不可用，属于环境问题，不影响测试代码结构正确性。
