# 进展记录

- 新增通用模块：`src/rag_stream/src/services/intent_recognizer.py`
- 复用接入：`src/rag_stream/src/services/intent_judgment.py`
- 新增单测：
  - `src/rag_stream/tests/test_intent_recognizer.py`
  - `src/rag_stream/tests/test_intent_judgment_general.py`
- 验证：`UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q tests/test_intent_recognizer.py tests/test_intent_judgment_general.py`
