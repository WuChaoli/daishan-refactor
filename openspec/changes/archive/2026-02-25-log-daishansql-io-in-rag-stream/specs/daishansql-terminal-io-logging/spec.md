## ADDED Requirements

### Requirement: DaiShanSQL Calls MUST Be Fully Instrumented In Rag Stream
The system MUST output terminal logs for input and output of every `DaiShanSQL` call in `src/rag_stream`, including `QueryBySQL`, `get_sql_result`, `judgeQuery`, and `sqlFixed` related invocations used by business modules.

#### Scenario: Covered call sites emit logs
- **WHEN** any covered `DaiShanSQL` method is invoked from `chat_general_service`, `source_dispath_srvice`, or `fetch_table_structures`
- **THEN** the system SHALL emit a pre-call input log and a post-call output log for that invocation

### Requirement: Input Log MUST Include Structured Invocation Context
The system MUST record invocation context in terminal logs using structured fields so engineers can map logs back to a concrete call site.

#### Scenario: QueryBySQL input is logged with context
- **WHEN** a `QueryBySQL(sql)` call is made
- **THEN** the input log SHALL include at least `call_site`, `method`, `args_preview` (including SQL preview), and `call_id`

### Requirement: Output Log MUST Include Result Summary And Duration
The system MUST record completion details for each call, including success state, result summary, and elapsed time.

#### Scenario: Successful call writes output summary
- **WHEN** a covered `DaiShanSQL` call returns successfully
- **THEN** the output log SHALL include at least `call_id`, `success=true`, `duration_ms`, and `result_preview`

### Requirement: Exception Paths MUST Be Logged Without Changing Business Semantics
The system MUST log exceptions for covered calls with invocation context and MUST re-raise the original exception to preserve existing behavior.

#### Scenario: Downstream call raises exception
- **WHEN** a covered `DaiShanSQL` call raises an exception
- **THEN** the system SHALL emit an error log containing `call_id`, `method`, `args_preview`, and error details
- **THEN** the original exception SHALL continue propagating to existing error handling paths

### Requirement: Large Payloads MUST Be Serialized And Truncated For Terminal Readability
The system MUST serialize complex input/output objects and truncate oversized payloads before writing terminal logs.

#### Scenario: Oversized SQL result is logged
- **WHEN** a call returns a large list/dict/string payload
- **THEN** the system SHALL output a readable preview not exceeding the configured/defined max length
- **THEN** truncated output SHALL indicate truncation explicitly
