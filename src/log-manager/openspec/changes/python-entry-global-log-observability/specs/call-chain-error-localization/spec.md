## ADDED Requirements

### Requirement: Call chain tree output
The system SHALL reconstruct and output a function call chain tree for traced executions.

#### Scenario: Trace renders hierarchical call chain
- **WHEN** a report is generated for a trace with nested calls
- **THEN** the report includes a hierarchical tree showing parent-child function relationships

### Requirement: Error propagation path output
The system MUST output an error path chain from the root function to the failing function when an error occurs.

#### Scenario: Error trace includes root-to-failure path
- **WHEN** an exception is captured within a traced call chain
- **THEN** the report includes a path view from root function to error function

### Requirement: Error location and context visibility
The system SHALL include error type, error message, and location hints, and MUST include nearest relevant marker context when available.

#### Scenario: Error report includes context and location hint
- **WHEN** an error event has marker and stack metadata
- **THEN** the report includes both location hints and nearest marker context

### Requirement: Terminal output contract
The system MUST format terminal lines as `[time] [level] [function] message`, with methods shown as `ClassName.func` and plain functions shown as `func`.

#### Scenario: Method and plain function formatting differs
- **WHEN** one terminal line comes from a class method and another from a plain function
- **THEN** the method line uses `ClassName.func` and the plain function line uses only `func`
