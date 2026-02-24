## Why

当前 `rag_stream` 的关键实现逻辑已分散在多个 `docs/contexts/*` 文档中，而 OpenSpec 侧为空。对后续进入项目的 AI 来说，缺少一个统一入口来理解 `src/rag_stream/src/services/chat_general_service.py` 的真实分流与降级契约，容易在后续开发中重复误判 `type=1/2/3` 路由行为。

本次变更聚焦“文档对齐”，把 `chat_general_service` 的实现逻辑沉淀到 OpenSpec 变更产物，形成可追踪、可复用的理解基线。

## What Changes

- 新建 OpenSpec 变更 `align-rag-stream-context-openspec`，用于承接 `chat_general_service` 的逻辑对齐说明。
- 在 proposal/design 中明确从 `chat_routes.chat_general` 到 `handle_chat_general` 的调用路径与职责边界，并固定权威入口文件：
  - `src/rag_stream/src/routes/chat_routes.py`（接口入口）
  - `src/rag_stream/src/services/chat_general_service.py`（业务分流入口）
- 文档化 `type=1`、`type=2(default)`、`type=3` 三条分支的输入条件、后处理动作、目标类别与失败降级。
- 文档化关键实现约束：
  - `request.question` 在意图识别前做园区词归一化，识别后恢复原问题。
  - 与 `DaiShanSQL.Server` 的 SQL 与 `judgeQuery` 调用均通过 `asyncio.to_thread` 包装。
  - 异常/空结果统一回落 `chat_with_category("通用", request)`。
- 明确 `docs/contexts` 与 OpenSpec 的关系：历史上下文保留，OpenSpec 作为后续 AI 的首要阅读入口。
- 记录本次范围决策：不修改 `docs/contexts/*` 文件，仅在 OpenSpec 变更内记录对齐策略与延期说明。

## Capabilities

### New Capabilities
- `rag-stream-chat-general-flow-knowledge`: 为 `chat_general_service` 提供结构化、可检索的实现逻辑知识入口（分流规则、降级规则、依赖关系、边界条件）。

### Modified Capabilities
- 无。

## Impact

- 主要影响文档与协作流程，不改动运行时代码。
- 影响范围：
  - `openspec/changes/align-rag-stream-context-openspec/proposal.md`
  - `openspec/changes/align-rag-stream-context-openspec/design.md`
  - `openspec/changes/align-rag-stream-context-openspec/specs/rag-stream-chat-general-flow-knowledge/spec.md`
  - `openspec/changes/align-rag-stream-context-openspec/tasks.md`
- 参考实现文件（仅用于事实锚点）：
  - `src/rag_stream/src/services/chat_general_service.py`
  - `src/rag_stream/src/routes/chat_routes.py`
- 外部接口、依赖版本、数据库结构均无变更。
