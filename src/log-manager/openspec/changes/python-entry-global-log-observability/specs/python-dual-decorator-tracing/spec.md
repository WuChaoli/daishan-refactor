## ADDED Requirements

### Requirement: Entry decorator creates isolated entry context
The system SHALL create a unique `entry_id` and start an isolated entry tracing context whenever an entry-decorated function is invoked.

#### Scenario: Entry invocation starts isolated context
- **WHEN** a function annotated as entry is called
- **THEN** the system creates an `entry_id` and records events to that entry context

### Requirement: Nested entry contexts are supported
The system SHALL support nested entry-decorated invocations and MUST route trace events to the innermost active entry context.

#### Scenario: Nested entry uses innermost context
- **WHEN** an entry-decorated function calls another entry-decorated function
- **THEN** trace events created within the inner scope are recorded under the inner `entry_id`

### Requirement: Context restoration after nested entry exit
The system SHALL restore the parent entry context after a nested entry scope exits.

#### Scenario: Parent context resumes after inner exit
- **WHEN** a nested entry-decorated function returns
- **THEN** subsequent trace events in the caller scope are recorded under the parent `entry_id`

### Requirement: Trace outside entry is captured globally
The system SHALL record trace-decorated function events to a global stream when no active entry context exists.

#### Scenario: No active entry falls back to global stream
- **WHEN** a trace-decorated function runs without any active entry context
- **THEN** its events are written to the global event stream
