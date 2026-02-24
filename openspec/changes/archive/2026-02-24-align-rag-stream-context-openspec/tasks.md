## 1. Flow Baseline Consolidation

- [x] 1.1 Confirm and record authoritative flow entrypoints from `src/rag_stream/src/routes/chat_routes.py` and `src/rag_stream/src/services/chat_general_service.py` in OpenSpec artifacts.
- [x] 1.2 Verify that OpenSpec documents the full branch map (`has_error`, `type=1`, `type=3`, `type=2/default`) with explicit trigger and routing outcomes.
- [x] 1.3 Verify that OpenSpec documents the request normalization-and-restore behavior around `intent_service.process_query` as part of flow baseline.

## 2. Branch Contract and Fallback Normalization

- [x] 2.1 Validate that `type=3` contract in OpenSpec explicitly covers `answer` prerequisite, return-question extraction, `judgeQuery` call, and prompt composition order.
- [x] 2.2 Validate that fallback-to-`chat_with_category("通用", request)` is defined as normative behavior for empty values and exceptions across all branches.
- [x] 2.3 Check that branch descriptions in proposal, design, and specs are semantically consistent and contain no contradictory routing statements.

## 3. Context Alignment and Adoption

- [x] 3.1 Define OpenSpec-first guidance for future analysis of chat-general routing and document `docs/contexts` as historical trace source.
- [x] 3.2 Add cross-reference notes from existing context docs to this OpenSpec change (or log explicit deferral decision) to reduce dual-entry ambiguity.
- [x] 3.3 Run a final artifact review to ensure proposal/design/specs/tasks remain documentation-only with no implied runtime code change.
