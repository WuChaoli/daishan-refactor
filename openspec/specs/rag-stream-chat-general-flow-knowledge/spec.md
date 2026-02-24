## Purpose
TBD - Canonical and current routing knowledge for chat_general flow.

## Requirements

### Requirement: Canonical Chat General Flow Knowledge
The project documentation system MUST provide a canonical and up-to-date description of the `chat_general` routing flow in OpenSpec for `src/rag_stream/src/services/chat_general_service.py`.

#### Scenario: AI agent reads canonical flow before analysis
- **WHEN** an AI agent or developer starts analysis for general chat routing behavior
- **THEN** the OpenSpec change artifacts SHALL describe the end-to-end flow from `chat_routes.chat_general` to `handle_chat_general`
- **THEN** the flow SHALL explicitly include intent processing, route decision, and fallback routing

### Requirement: Branch Decision Contract Is Explicit
The OpenSpec documentation MUST define branch-level contracts for `has_error`, `type=1`, `type=3`, and `type=2/default` in a way that can be mapped to code behavior.

#### Scenario: Reader verifies type-based behavior
- **WHEN** a reader inspects branch logic in OpenSpec artifacts
- **THEN** each branch SHALL include trigger condition, processing action, target category, and fallback condition
- **THEN** `type=3` SHALL include the documented dependency on `answer` extraction and `judgeQuery` result composition

### Requirement: Normalization And Restore Behavior Is Documented
The OpenSpec documentation MUST define request normalization and restoration behavior around intent processing.

#### Scenario: Reader verifies normalization window
- **WHEN** a reader checks the flow baseline for `handle_chat_general`
- **THEN** the artifacts SHALL state that request text normalization happens before `intent_service.process_query`
- **THEN** the artifacts SHALL state that original question text is restored before downstream routing execution

### Requirement: Fallback Behavior Is Normative
The OpenSpec documentation MUST state fallback behavior as normative rules, not optional guidance.

#### Scenario: Exceptional or incomplete branch result
- **WHEN** a branch cannot produce a valid routed request because of missing data, empty result, or exception
- **THEN** the artifacts SHALL state that routing falls back to `chat_with_category("通用", request)`
- **THEN** this fallback rule SHALL be represented consistently across proposal and design references

### Requirement: Context Alignment Between OpenSpec and Historical Docs
For this capability, OpenSpec SHALL be the primary entry for current routing knowledge, while `docs/contexts` SHALL be treated as historical trace context.

#### Scenario: Reader chooses documentation entry point
- **WHEN** a reader needs to understand current `chat_general_service` behavior
- **THEN** OpenSpec artifacts SHALL be identified as the first-entry source
- **THEN** historical context documents SHALL be referenced as secondary, traceable background

### Requirement: Deferral Decisions Must Be Recorded
When cross-references to legacy context documents are intentionally deferred, the decision MUST be recorded in the active OpenSpec design artifact.

#### Scenario: Cross-reference update intentionally deferred
- **WHEN** context cross-link updates are not applied in current implementation scope
- **THEN** design artifact SHALL include an explicit deferral note and rationale
- **THEN** the deferral note SHALL indicate that no runtime behavior change is introduced by the deferral
