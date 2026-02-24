## ADDED Requirements

### Requirement: Chain-aware event identity fields
The system MUST include `session_id`, `run_id`, `trace_id`, `span_id`, `pid`, and `tid` in all chain-participating events.

#### Scenario: Call event includes chain identity
- **WHEN** the system records a call lifecycle event
- **THEN** the event payload includes all required chain identity fields

### Requirement: Parent-child span linkage
The system SHALL include `parent_span_id` for non-root spans and MUST allow empty `parent_span_id` for root spans.

#### Scenario: Child span references parent
- **WHEN** a traced function is invoked within another traced function
- **THEN** the child event records the caller span as `parent_span_id`

### Requirement: Event type coverage
The system MUST support event types `call_enter`, `call_exit`, `error`, `marker`, and `process_mem`.

#### Scenario: Error event is normalized
- **WHEN** a traced function raises an exception
- **THEN** the system writes an `error` event in the normalized event model

### Requirement: Deterministic storage layout
The system SHALL store entry-scoped events and global events in separate paths under the session directory.

#### Scenario: Entry and global streams are separated
- **WHEN** an entry-scoped event and a global fallback event are emitted in the same session
- **THEN** the events are written to separate entry and global stream files
