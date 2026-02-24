## ADDED Requirements

### Requirement: Process-level memory sampling
The system SHALL capture process memory metrics during runtime and MUST include RSS in process memory events.

#### Scenario: Process memory event includes RSS
- **WHEN** a process memory sampling tick occurs
- **THEN** the emitted `process_mem` event includes current RSS value

### Requirement: Span-level memory delta tracking
The system SHALL record memory at function entry and exit and MUST provide span memory delta for traced calls.

#### Scenario: Traced call reports memory delta
- **WHEN** a traced function exits
- **THEN** the corresponding call lifecycle data includes entry memory, exit memory, and delta values

### Requirement: Mode-based overhead control
The system MUST provide at least `lite` and `enhanced` modes for memory observability behavior.

#### Scenario: Lite mode uses lower collection overhead
- **WHEN** the system runs in `lite` mode
- **THEN** memory collection uses conservative defaults intended for lower runtime overhead

### Requirement: Memory feature toggles
The system SHALL expose independent toggles for process memory collection, span memory collection, and chain memory reporting.

#### Scenario: Span memory collection can be disabled independently
- **WHEN** span memory collection toggle is disabled
- **THEN** process memory events may continue while span memory fields are not emitted
