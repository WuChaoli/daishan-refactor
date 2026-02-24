## Context

`/api/general` 的路由入口位于 `src/rag_stream/src/routes/chat_routes.py`，核心分流编排位于 `src/rag_stream/src/services/chat_general_service.py`。近期该链路涉及 `type=3` 分流增强、优先阈值相关行为调整、`DaiShanSQL` 导入路径修复等变更，导致理解信息分散在代码与多个 `docs/contexts/*` 文档中。

为降低后续 AI 进入成本，本设计将 OpenSpec 作为当前行为契约的统一入口，并以代码实现为唯一事实锚点。

**Authoritative Entrypoints**
- API entrypoint: `chat_routes.chat_general` (`src/rag_stream/src/routes/chat_routes.py`)
- Orchestration entrypoint: `handle_chat_general` (`src/rag_stream/src/services/chat_general_service.py`)

当前主流程：

```text
chat_routes.chat_general
  -> handle_chat_general
     -> (normalize request.question)
     -> intent_service.process_query
     -> (restore original request.question)
     -> route decision by has_error/type
        -> type1: _post_process_and_route_type1 -> _route_with_sql_result
        -> type3: _post_process_and_route_type3 -> chat_with_category("通用", updated_request)
        -> type2/default: _post_process_and_route_type2 -> _route_with_sql_result("通用")
        -> any failure: fallback chat_with_category("通用", request)
```

## Goals / Non-Goals

**Goals:**
- 为后续开发 AI 提供单一入口，快速理解 `chat_general_service` 的真实实现逻辑。
- 统一表达三类分流的触发条件、数据拼接规则、目标类别与异常降级路径。
- 固化“OpenSpec 前置、`docs/contexts` 追溯”的文档协作边界。
- 在不改业务代码的前提下，完成本次文档对齐实现清单。

**Non-Goals:**
- 不改动 `chat_general_service.py` 任何运行逻辑。
- 不新增/修改 API、配置项、数据库或外部依赖。
- 不执行业务功能实现或运行时测试变更。

## Decisions

### Decision 1: Code-First Anchoring
- 结论：文档事实以 `chat_routes.py` 与 `chat_general_service.py` 为权威入口，不以历史说明文档作为主索引。
- 原因：代码是当前行为真相，历史文档存在滞后可能。
- 备选：从 `docs/contexts` 汇总逆推。
- 未选原因：容易引入二次转述偏差。

### Decision 2: Branch Contract Matrix as Normative Map
- 结论：使用分支矩阵显式定义触发条件、动作、目标类别、失败回落。
- 原因：便于 AI 快速映射 `has_error/type` 行为并进行影响分析。

```text
branch                trigger                               action                                                target              fallback
--------------------------------------------------------------------------------------------------------------------------------------------------
has_error=true         result_dict.data.error                skip intent result and direct route                  通用                unconditional

type=1                 result_type == 1                      extract kb + SQL enrichment via _route_with_sql      kb_name             any empty/exception -> 通用

type=3                 result_type == 3                      validate answer/returnQuestion -> judgeQuery ->       通用(updated req)    any empty/exception -> 通用
                                                             compose: answer + judge_result + original_question

type=2/default         else                                  get_sql_result + _route_with_sql_result               通用                any empty/exception -> 通用
```

### Decision 3: Normalization/Restore Contract
- 结论：将“归一化后识别、识别后恢复原问题”定义为文档契约。
- 约束：`request.question` 只在 `intent_service.process_query` 期间使用归一化文本，后续分流基于恢复后的原始问题。

### Decision 4: Type-3 Contract Detail
- 结论：`type=3` 必须满足以下顺序：
1. `answer` 非空。
2. 从 `results[0].question` 提取 `return_question`。
3. 调用 `judgeQuery(request.question, return_question)`。
4. 按 `answer + "\n\n" + judge_result + "\n\n" + request.question` 拼接。
5. 路由到 `chat_with_category("通用", updated_request)`。
- 异常策略：任一环节失败均回落 `chat_with_category("通用", request)`。

### Decision 5: OpenSpec-First with Context Deferral Log
- 结论：后续分析默认先读 OpenSpec；`docs/contexts` 仅作历史追溯。
- 延期说明（对应任务 3.2）：按本次用户决策，不修改现有 `docs/contexts/*` 文件，仅在本变更内记录延期互链决策。

## Risks / Trade-offs

- [Risk] 后续代码改动后 OpenSpec 可能过期。
  -> Mitigation: 凡涉及 `has_error/type1/type2/type3` 逻辑变更，必须同步更新对应 OpenSpec 变更。

- [Risk] 未在 `docs/contexts` 添加互链，仍可能存在双入口惯性。
  -> Mitigation: 在后续文档治理任务中单独处理互链补充，并保持本变更的延期记录。

## Migration Plan

1. 使用当前变更完成 proposal/specs/design/tasks 的文档对齐实施。
2. 后续涉及 `chat_general_service` 逻辑讨论时，统一引用本变更作为入口。
3. 若进入发布流程，按需要执行 `/opsx:archive align-rag-stream-context-openspec`。
4. 若后续出现行为变更，以新变更增量维护，避免覆盖既有决策历史。

## Open Questions

- 是否在下一轮独立变更中补齐 `docs/contexts/*` 到 OpenSpec 的互链落地？

## Final Review (Documentation-Only)

- proposal/design/specs/tasks 均仅描述行为契约与协作流程。
- 本变更不包含运行时代码、配置、数据库或 API 变更。
- 本次实施的“完成”定义为文档一致性与任务清单闭环，而非功能发布。
