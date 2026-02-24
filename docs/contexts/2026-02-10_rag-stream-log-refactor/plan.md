# RAG Stream 日志优化实施计划

## 目标

在 `src/rag_stream` 中优化日志策略，减少由过渡函数导致的日志噪音，同时补充业务语义日志，提升问题排查效率与业务链路可观测性。

## 策略

1. 保留入口函数与核心编排函数的 `@log`，用于调用链追踪。
2. 移除“纯透传/薄包装”函数上的 `@log`（仅做参数转发与返回）。
3. 在关键业务节点使用 `from log_decorator import logging` 的 `logging.INFO/DEBUF/WARNING/ERROR` 输出业务数据。
4. 优先记录：业务分支、资源/实体数量、会话ID/请求ID、关键状态变化。

## 已完成（第 1 批）

### 范围

- `src/rag_stream/src/routes/chat_routes.py`
- `src/rag_stream/src/services/source_dispath_srvice.py`

### 结果

- 移除多个纯透传路由函数 `@log`（例如仅转调 `chat_with_category` 的函数）。
- 保留入口链路 `@log(is_entry=True, enable_mermaid=True)`。
- 在关键流程补充业务日志：
  - 分类路由命中、会话创建结果、资源调度开始/结束
  - 并行分析结果、分发路径命中、SQL查询行数、AI筛选结果

## 已完成（第 2 批）

### 范围

- `src/rag_stream/src/services/personnel_dispatch_service.py`
- `src/rag_stream/src/services/rag_service.py`

### 结果

- `personnel_dispatch_service.py`
  - 保留主函数 `handle_personnel_dispatch` 的 `@log`
  - 移除私有 helper 的 `@log`
  - 增加实体提取/并行调用/结果汇总的业务日志
- `rag_service.py`
  - 移除 `get_rag_client` 上的 `@log`（薄包装）
  - 保留 `create_rag_session`、`get_or_create_session`、`stream_chat_response` 的 `@log`
  - 增加会话创建与流式响应生命周期业务日志

## 已完成（第 3 批）

### 范围

- `src/rag_stream/src/utils/session_manager.py`
- `src/rag_stream/src/utils/ragflow_client.py`

### 结果

- `session_manager.py`
  - 移除高噪音/薄包装函数 `@log`：`__init__`、`update_session_activity`、`cleanup_expired_session`、`cleanup_all_expired_sessions`、`get_user_sessions_info`
  - 保留关键对外会话编排函数 `@log`：`create_session`、`get_user_session`、`cleanup_user_sessions`
  - 增加业务日志：会话命中/未命中、过期清理触发、批量清理数量、用户会话查询数量、批量清理计数
- `ragflow_client.py`
  - 移除薄包装/纯工具函数 `@log`：`_parse_similarity`、`test_connection`
  - 保留关键链路函数 `@log`：`_get_datasets`、`query_all_databases`、`query_single_database`、`_query_with_sdk`
  - 增加业务日志：知识库配置数量与缺失数量、并行查询数据库数/结果数/异常数、单库查询结果/超时/失败原因、SDK chunk 返回计数

### 本批验证

- 语法检查：`python -m py_compile src/rag_stream/src/utils/session_manager.py src/rag_stream/src/utils/ragflow_client.py` ✅
- 定向测试（.venv）：
  - `./.venv/bin/python -m pytest -q tests/test_solid_resource_modification.py tests/test_async_route_decorator.py` ✅ `1 passed, 8 warnings in 0.47s`
- 导入检查（带 PYTHONPATH）：`PYTHONPATH=src/rag_stream python -c "import importlib; importlib.import_module('src.utils.session_manager'); importlib.import_module('src.utils.ragflow_client')"` ✅

## 已完成（第 4 批：入口函数日志增强）

### 范围

- `src/rag_stream/src/routes/chat_routes.py`

### 结果

- 入口函数 `@log` 参数调整（减少流式返回体日志噪音）：
  - `chat_with_category`、`chat_general`、`people_dispatch`、`source_dispatch`、`health_check`
  - 统一为 `@log(is_entry=True, enable_mermaid=True, print_result=False)`
- 入口业务日志增强（沿用本任务字段风格）：
  - `chat_with_category`：新增 `question_len`，补充不支持类别告警、流式响应启动日志
  - `chat_general`：补充 `has_user_id`，新增 `intent_service` 缺失错误日志与路由完成日志
  - `people_dispatch`：补充输入长度、空输入拒绝告警、结果计数/类型日志
  - `source_dispatch`：补充 `has_voice_text`，输出包含事故ID与资源类型的完成日志
  - `health_check`：使用聚合变量记录会话/用户数量并输出 `INFO` 级业务日志
- 薄包装函数 `@log` 清理：
  - 移除 `get_categories` 的 `@log`（纯返回配置数据）

### 本批验证

- 语法检查（.venv）：
  - `./.venv/bin/python -m py_compile src/rag_stream/src/routes/chat_routes.py src/rag_stream/src/utils/session_manager.py src/rag_stream/src/utils/ragflow_client.py` ✅
- 定向测试（.venv）：
  - `./.venv/bin/python -m pytest -q tests/test_solid_resource_modification.py tests/test_async_route_decorator.py` ✅ `1 passed, 8 warnings in 0.66s`

## 已完成（第 5 批：DHC 入口函数日志增强）

### 范围

- `src/Digital_human_command_interface/src/api/routes.py`

### 结果

- 入口函数 `@log` 参数统一优化（降低返回体日志噪音）：
  - `intent_handler_0`、`intent_handler_1`、`intent_handler_2`、`instruct_process`
  - `root`、`health_check`、`intent_recognition`、`instrcution_command`
  - 全部调整为 `@log(is_entry=True, enable_mermaid=True, print_result=False)`
- 入口业务日志增强（沿用本任务字段模板）：
  - 记录入口请求上下文（`user_id`/`query_len`/`text_len`）
  - 记录关键分支（空结果、客户端缺失、降级路径、未知意图类型）
  - 记录关键状态（意图类型、候选数量、健康检查状态、流式转发开始）
  - 记录失败摘要（初始化失败、流式处理异常、Dify/DaiShanSQL 异常）
- 薄包装函数 `@log` 清理：
  - 移除 `create_dify_payload`、`get_dify_headers` 的 `@log`（纯参数组装）
- 调试输出清理：
  - 移除运行时 `print(...)`，替换为 `logging.DEBUF/ERROR`

### 本批验证

- 语法检查（.venv）：
  - `./.venv/bin/python -m py_compile src/Digital_human_command_interface/src/api/routes.py src/rag_stream/src/routes/chat_routes.py src/rag_stream/src/utils/session_manager.py src/rag_stream/src/utils/ragflow_client.py` ✅
- 定向测试（.venv）：
  - `./.venv/bin/python -m pytest -q tests/test_solid_resource_modification.py tests/test_async_route_decorator.py` ✅ `1 passed, 8 warnings in 0.34s`

## 验证策略

- 语法检查：`python -m py_compile`（变更文件）
- 定向回归：`tests/test_solid_resource_modification.py`、`tests/test_async_route_decorator.py`
- 导入检查：按环境可用性执行（外部依赖缺失时记录阻塞）

## 风险与控制

- 风险：过度删除 `@log` 可能降低定位粒度。
- 控制：仅删除薄包装函数，核心编排节点保留 `@log`。
- 风险：业务日志过多造成新噪音。
- 控制：以“关键业务指标”优先，避免重复输出完整大对象。
