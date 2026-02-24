## ADDED Requirements

### Requirement: Incremental analysis for long-running processes
The system SHALL perform report analysis incrementally and MUST NOT require all processes in a session to exit before generating reports.

#### Scenario: Reports generated while process is still running
- **WHEN** a monitored process remains active
- **THEN** the system still produces report snapshots according to trigger policy

### Requirement: Multi-trigger report generation policy
The system MUST support timer trigger, event-count trigger, idle trigger, and immediate trigger for critical errors.

#### Scenario: Event threshold trigger runs analysis
- **WHEN** new events since the last snapshot reach configured threshold `N`
- **THEN** the system runs incremental analysis and generates a new report snapshot

### Requirement: File-first reporting output
The system SHALL write complete reports to local files and MUST avoid printing full report bodies to terminal output.

#### Scenario: Full report is persisted to file
- **WHEN** a new snapshot report is generated
- **THEN** the report content is written to the configured report file path

### Requirement: Per-entry and global summary outputs
The system SHALL generate per-entry reports and a global summary report focused on error aggregation.

#### Scenario: Session with multiple entries produces both report types
- **WHEN** a session contains events from one or more entry contexts
- **THEN** the system outputs entry-scoped reports and a global error summary report

### Requirement: Chinese report language
The system SHALL produce human-readable report content in Chinese.

#### Scenario: Generated report uses Chinese labels
- **WHEN** the system writes a report snapshot
- **THEN** report section titles and narrative output are rendered in Chinese
