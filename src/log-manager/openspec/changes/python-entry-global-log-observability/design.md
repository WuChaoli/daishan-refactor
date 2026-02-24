## Context

This change introduces a Python-first observability design for local troubleshooting in long-running processes. The current state relies on ad hoc logs and manual tracing, which makes it hard to reconstruct function call paths, parameter context, and error propagation quickly.

Key constraints:
- Runtime overhead must stay low during business execution.
- Processes may run continuously; reporting cannot depend on global process exit.
- Output is file-first (not full terminal report), with Chinese report content.
- Function display must follow: class methods as `ClassName.func`, plain functions as `func`.

Primary stakeholders:
- Local developers diagnosing function behavior and failures.
- Operations engineers troubleshooting service incidents in local or pre-prod environments.

## Goals / Non-Goals

**Goals:**
- Provide a dual-decorator model (`entry` + `trace`) with deterministic routing for nested and non-entry execution.
- Capture structured chain-aware events that support call tree reconstruction and error path localization.
- Add incremental report generation for continuously running processes.
- Produce per-entry reports plus global error summaries.
- Include process-level and span-level memory observability with configurable overhead.

**Non-Goals:**
- Real-time dashboarding or alerting platform features.
- Full APM parity (distributed tracing backend, fleet-wide correlation, SaaS analytics).
- Centralized multi-team log aggregation in this phase.

## Decisions

### 1) Instrumentation model: dual decorators with nested entry support

Decision:
- Use two decorators:
  - `entry` for business entry points with isolated logging/report context.
  - `trace` for regular function tracing.
- Allow nested entries; route `trace` events to the innermost active entry.
- If no active entry exists, route to global logs.

Rationale:
- Matches the required "entry-isolated + global fallback" workflow.
- Preserves business boundaries while retaining visibility for utility/background calls.

Alternatives considered:
- Single universal decorator:
  - Simpler API, but cannot express entry-level isolation and nested routing clearly.
- Fully automatic instrumentation:
  - Lower manual effort, but less predictable boundaries and higher rollout risk for MVP.

### 2) Correlation identifiers and chain model

Decision:
- Require `session_id`, `run_id`, `trace_id`, `span_id`, `parent_span_id`, `pid`, `tid` on traceable events.
- `run_id` is per process. `session_id` groups all processes in one troubleshooting session.

Rationale:
- Supports both local process analysis and cross-process session grouping.
- Enables deterministic reconstruction of call trees and error propagation chains.

Alternatives considered:
- Process-only IDs (`pid`/`tid`) without chain IDs:
  - Insufficient for reliable nested call reconstruction.
- Global single run identifier only:
  - Ambiguous for long-running multi-process lifecycle boundaries.

### 3) Event model and storage layout

Decision:
- Event types for MVP: `call_enter`, `call_exit`, `error`, `marker`, `process_mem`.
- Store entry streams separately from global fallback stream:
  - `runs/<session>/entries/<entry_id>.events.jsonl`
  - `runs/<session>/global.events.jsonl`

Rationale:
- Clear separation between entry-centric analysis and catch-all global tracing.
- JSONL keeps artifacts human-inspectable for local debugging.

Alternatives considered:
- Single merged event file:
  - Simpler storage, but harder per-entry analysis and higher parsing noise.
- Binary-only format:
  - Better compactness but weaker inspectability for early-stage debugging.

### 4) Reporting strategy: incremental, file-first, error-priority

Decision:
- Run incremental analysis via trigger policy:
  - timer (`T=60s`), event threshold (`N=5000`), idle window (`I=10s`), critical-error immediate trigger.
- Write reports to files only (no full terminal dump):
  - per-entry report snapshots
  - global error summary snapshots
- Keep latest plus rolling history (`K=20` snapshots).

Rationale:
- Works for continuously running processes.
- Prioritizes actionable troubleshooting outputs without flooding terminal logs.

Alternatives considered:
- End-of-run report only:
  - Not usable for daemons/long-running workers.
- Terminal-first full reports:
  - Poor usability for large outputs and high event volume.

### 5) Memory observability with overhead controls

Decision:
- Capture process memory samples and span memory deltas:
  - process metrics (e.g., RSS) through `process_mem`
  - `mem_enter_rss_kb`, `mem_exit_rss_kb`, `mem_delta_rss_kb` on call lifecycle
- Provide mode switches:
  - `lite` (default low-overhead)
  - `enhanced` (higher-fidelity diagnostics)
- Add feature toggles for memory/report/console options.

Rationale:
- Meets explicit requirement for both process-level and call-chain memory visibility.
- Keeps overhead tunable by scenario.

Alternatives considered:
- Always-on high-frequency memory sampling:
  - Better granularity but too expensive for default operation.
- Process-level memory only:
  - Fails to explain which function chain likely drove growth.

### 6) Terminal message contract

Decision:
- Standardize terminal output as:
  - `[time] [level] [function] message`
- Function rendering:
  - class methods: `ClassName.func`
  - plain functions: `func`

Rationale:
- Keeps terminal output compact and predictable while preserving operator context.

Alternatives considered:
- Include module/package path in terminal:
  - More detail, but reduces scanability and violates requested format preference.

## Risks / Trade-offs

- [Risk] Entry decorators are applied inconsistently, causing partial call trees  
  -> Mitigation: document entry selection guidelines and provide validation warnings in reports for orphan-heavy traces.

- [Risk] Memory delta on spans can be noisy due to GC and concurrent activity  
  -> Mitigation: label span memory as approximate and combine with process trend views.

- [Risk] Event volume spikes may increase I/O overhead  
  -> Mitigation: batch writes, threshold-trigger analysis, and default `lite` mode.

- [Risk] Nested entry routing complexity can introduce misclassification bugs  
  -> Mitigation: enforce stack-based routing semantics and include route-source metadata in debug mode.

- [Risk] Continuous snapshots can consume disk space over long sessions  
  -> Mitigation: rolling retention (`K`) and prune policy for stale sessions.

## Migration Plan

1. Add specification artifacts for each capability defined in proposal (`specs/...`).
2. Implement instrumentation contracts (`entry`, `trace`, event shape, routing rules).
3. Add incremental analyzer and report writers (per-entry and global summary).
4. Enable memory signals and mode/toggle controls with conservative defaults.
5. Roll out in `lite` mode by default; validate overhead and report quality with sample long-running workloads.
6. Rollback strategy: disable decorators/toggles to stop new instrumentation and keep existing reports as static artifacts.

## Open Questions

- Should memory metrics require an external package (e.g., `psutil`) or support a fallback path with reduced fidelity?
- What is the minimum required marker taxonomy for consistent cross-team report readability?
- Do we need optional module path inclusion in reports (not terminal) for faster code navigation?
- Should global error summaries aggregate by error signature only, or by `error signature + function` key?
