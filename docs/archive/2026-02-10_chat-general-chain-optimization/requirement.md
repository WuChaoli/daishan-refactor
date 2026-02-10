# 需求说明：/api/general 接口链路优化

## 背景

当前 `/api/general` 链路存在以下问题：

1. 路由层直接初始化 `intent_service`，与应用生命周期初始化形成双实例来源。
2. `handle_chat_general` 在异常和部分分支中返回 `None`，导致上层响应语义不稳定。
3. `_route_with_sql_result` 重新构建 `ChatRequest` 时丢失 `session_id`、`stream` 字段。

## 目标

1. 将 `intent_service` 统一为应用生命周期管理，并从 `app.state` 注入路由。
2. 让 `handle_chat_general` 在意图错误、后处理失败或空 SQL 结果场景下稳定回退到 `通用` 路由。
3. 保证请求透传字段完整，避免会话和流式配置丢失。

## 非目标

1. 不改动意图识别算法和阈值策略。
2. 不改动 `chat_with_category` 的主流程结构。
3. 不进行全链路性能压测。

## 验收标准

1. 新增测试覆盖上述三个问题场景，测试通过。
2. `/api/general` 和 `/api/guess-questions` 不再使用模块级 `intent_service` 单例。
3. 关键路径异常时不返回 `None`，而是回退到可用分类路由。
