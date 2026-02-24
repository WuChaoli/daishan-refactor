# 设计文档

## 测试设计

### 1. 测试类型

- 采用集成测试，直接实例化：
  - `RagflowClient(settings.ragflow, settings.intent)`
  - `IntentService(ragflow_client=...)`
- 通过真实 `process_query` 调用验证返回意图类别。

### 2. 用例组织

- 使用 `pytest.mark.parametrize` 承载整批问句。
- 每条问句执行一次 `process_query`，断言 `result["type"] == 3`。

### 3. 运行控制

- 集成测试默认关闭，使用环境变量开关：
  - `RUN_RAGFLOW_INTENT_INTEGRATION=1`
- 未开启时统一 `skip`，避免默认测试流程访问外部依赖。

### 4. 前置校验

- 检查 `settings.ragflow.base_url`、`settings.ragflow.api_key` 是否存在。
- 检查 `ragflow.database_mapping["岱山-指令集-固定问题"]` 是否为 `3`。

### 5. 输出与定位

- 测试文件路径：
  - `test/2026-02-24_intent-service-type3-integration/test_intent_service_type3_integration.py`
- 采用失败信息携带原问句与完整返回，便于定位误判。
