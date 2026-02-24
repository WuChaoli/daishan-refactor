## Why

Local developers and operations engineers currently cannot quickly reconstruct function call paths, parameter context, and precise error locations during troubleshooting without adding heavy instrumentation. We need a low-overhead Python-first observability workflow that records minimal runtime events and continuously produces actionable local reports for long-running processes.

## What Changes

- Introduce a dual-decorator tracing model for Python:
  - entry decorator for business entry points with isolated logs per entry
  - regular decorator for function-level tracing routed to active entry context or global logs
- Support nested entry contexts and deterministic event routing for nested and non-entry execution.
- Define a structured event model for call lifecycle, errors, markers, and process memory signals.
- Add incremental report generation that does not wait for process termination, with time-based, event-count, and idle triggers.
- Produce localized (Chinese) text reports to files:
  - per-entry execution reports (including call chains)
  - global error summary report
- Standardize terminal output format to include time, level, function identifier, and message.
- Add memory observability for both process-level usage and call-chain/span-level memory deltas.
- Provide observability mode switches (`lite` and `enhanced`) and feature toggles for memory/report/console behavior.

## Capabilities

### New Capabilities

- `python-dual-decorator-tracing`: Define and enforce `entry` + `trace` decorator behavior, nested entry handling, and routing rules to entry/global logs.
- `structured-event-and-routing`: Define event schema, required chain identifiers, levels, function naming rules, and file layout for entry/global event streams.
- `incremental-local-reporting`: Define periodic and on-trigger incremental analysis, per-entry Chinese reports, and global error-focused summaries.
- `call-chain-error-localization`: Define required outputs for function call chain trees, error propagation paths, and contextual error localization.
- `memory-observability-controls`: Define process memory metrics, span memory deltas, and mode/toggle requirements for low-overhead vs enhanced collection.

### Modified Capabilities

- None.

## Impact

- Affected systems:
  - Python runtime instrumentation interface (decorators and marker API)
  - Local event buffering/routing and storage layout under `.log-manager/`
  - Incremental analysis and report-generation pipeline
  - Console output formatting rules
- Potential dependency impact:
  - May require a process memory metrics provider (for example, `psutil`) depending on final design choices.
- Operational impact:
  - Adds continuous local report snapshots for long-running processes
  - Improves troubleshooting speed by prioritizing call-chain and error-path visibility.
