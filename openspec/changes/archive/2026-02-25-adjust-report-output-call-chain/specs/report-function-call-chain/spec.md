## ADDED Requirements

### Requirement: Entry report uses YAML structure
The system MUST replace the current sectioned plain-text entry report content with a YAML document while keeping existing report file paths unchanged.
The YAML document MUST include top-level keys: `metadata`, `error_summary`, `call_chain`, `error_path`, and `chain_memory_top`.

#### Scenario: Entry report is generated as YAML
- **WHEN** `flush_reports()` generates an entry report from collected runtime events
- **THEN** the report file content is parseable as YAML and contains the required top-level keys

### Requirement: Call chain node contract
The system SHALL output function call chains as hierarchical YAML nodes.
Each node MUST include fields `function_name`, `duration_ms`, and `exception`.
Each node SHOULD include `children` for nested calls; `children` MUST be an array when present.

#### Scenario: Nested function calls are represented with required fields
- **WHEN** a traced entry contains nested parent-child function calls
- **THEN** each node in the generated `call_chain` includes `function_name`, `duration_ms`, and `exception`

### Requirement: Exception field semantics
The system MUST encode node exception information in the `exception` field.
If no exception is observed for a node, `exception` MUST be `null`.
If an exception is observed, `exception` MUST include `type` and `message`.

#### Scenario: Error node contains structured exception data
- **WHEN** an exception is raised within a traced call chain
- **THEN** the failing node has `exception.type` and `exception.message` and non-failing nodes use `exception: null`

### Requirement: Legacy plain-text headings are removed
The system MUST remove legacy plain-text heading output from entry reports, including headings such as `【函数调用链】` and `【错误路径链】`.

#### Scenario: Generated report no longer includes legacy headings
- **WHEN** a new entry report is generated after this change
- **THEN** the report content does not contain legacy section heading markers and only contains YAML-structured report content
