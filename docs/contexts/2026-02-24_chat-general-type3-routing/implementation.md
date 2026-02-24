# 实施记录

## 代码变更
- `src/rag_stream/src/services/intent_service/intent_service.py`
  - 新增 `_extract_answer_from_question_text`。
  - `_post_process_result` 增加顶层 `answer` 输出。

- `src/rag_stream/src/services/chat_general_service.py`
  - 新增 `_extract_question_from_qa_text`。
  - 新增 `_post_process_and_route_type3`。
  - `handle_chat_general` 增加 `result_type == 3` 分支。

- `src/rag_stream/config.yaml`
  - `ragflow.database_mapping` 补充 `岱山-指令集-固定问题: 3`。
  - 修复根因：RagflowClient 仅加载配置映射中声明的知识库，缺失该项时 type=3 候选库不会被查询。

## 测试变更
- `src/rag_stream/tests/test_chat_general_service.py`
  - 新增 type=3 成功分流测试。
  - 新增 type=3 answer 缺失降级测试。
  - 新增 type=3 judgeQuery 异常降级测试。

- `src/rag_stream/tests/test_intent_service_type3.py`
  - 新增“映射命中固定问题库返回 type=3”测试。
  - 新增“无 Answer 片段时返回空 answer”测试。

## 验证计划
- 运行：
  - `./.venv/bin/pytest src/rag_stream/tests/test_chat_general_service.py`
  - `./.venv/bin/pytest src/rag_stream/tests/test_intent_service_type3.py`

## 复测结果（修复后）
- 批量 40 条问题重测：
  - `type=3`: 32
  - `type=2`: 8
  - `type=1`: 0
