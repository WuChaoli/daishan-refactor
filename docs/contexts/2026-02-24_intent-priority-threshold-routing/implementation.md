# 实施记录

## 代码变更

- `src/rag_stream/src/services/intent_service/base_intent_service.py`
  - `IntentRecognizerSettings` 新增 `priority_similarity_threshold` 字段（默认 `0.7`）。
  - JSON 加载逻辑新增读取 `priority_similarity_threshold`。

- `src/rag_stream/src/services/intent_service/intent_service.py`
  - 重写 `_judge_daishan_intent_priority`：先判两个优先库，再全局降级。
  - `_load_process_settings` 中记录是否启用岱山优先规则。
  - 启用 `_get_process_judge_function`，按映射条件返回自定义判定函数。
  - `_should_use_daishan_priority` 改为检查两张优先表。

- `src/rag_stream/src/services/intent_mapping.example.json`
  - 新增 `priority_similarity_threshold: 0.7`。

- `src/rag_stream/tests/test_intent_service_type3.py`
  - 增加优先阈值与降级逻辑测试用例。

## 验证计划

- 执行 `src/rag_stream/tests/test_intent_service_type3.py`，验证优先阈值命中与降级路径。
