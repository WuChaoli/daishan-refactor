# 设计与实施方案：/api/general 接口链路优化

## 总体方案

采用“低风险渐进重构”：

1. 先以测试锁定行为（RED）。
2. 在 `chat_general_service` 做最小逻辑改造（GREEN）。
3. 再将 `intent_service` 注入方式收敛到 `app.state`。

## 链路优化点

### 1) 服务注入统一化

- 问题：`chat_routes.py` 内部直接初始化 `IntentService`，与 `main.py` 生命周期初始化并存。
- 方案：
  - 在 `main.py` 启动时将 `intent_service` 挂载到 `app.state.intent_service`。
  - 在 `chat_general`、`guess_questions` 路由函数中通过 `Request` 获取服务实例。
  - 缺失时返回 `500`，信息明确为“intent_service 未初始化”。

### 2) 回退语义稳定化

- 问题：`handle_chat_general` 在意图错误或异常时返回 `None`。
- 方案：
  - 意图错误（`data.error`）直接回退 `chat_with_category("通用", request)`。
  - type1/type2 后处理返回 `None` 时统一回退 `通用`。
  - 捕获异常后也统一回退 `通用`，保证结果可用。

### 3) 请求透传完整化

- 问题：`_route_with_sql_result` 构造新请求时丢失 `session_id` 与 `stream`。
- 方案：
  - 附加 SQL 结果时同时保留 `session_id`、`user_id`、`stream`。
  - 当 SQL 结果为空时直接使用原请求继续路由，不中断调用链。

## 测试策略

新增 `src/rag_stream/tests/test_chat_general_service.py`，覆盖：

1. SQL 路由时字段透传完整。
2. 意图错误时回退到通用分类。
3. SQL 空结果时仍可回退通用分类。

## 风险与回滚

- 风险：`app.state` 注入依赖应用生命周期，若测试绕过 lifespan 需显式兜底。
- 回滚：单文件回退 `chat_general_service.py` / `chat_routes.py` / `main.py` 即可。
