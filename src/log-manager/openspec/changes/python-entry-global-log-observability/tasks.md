## 1. Instrumentation Foundation

- [x] 1.1 Define decorator interfaces for `entry` and `trace` with shared runtime context contract
- [x] 1.2 Implement context lifecycle management for `session_id`, per-process `run_id`, and trace/span identity propagation
- [x] 1.3 Implement nested entry stack handling so innermost entry context is always active for scoped traces
- [x] 1.4 Implement plain-function and class-method function identifier normalization (`func` vs `ClassName.func`)

## 2. Event Model and Routing

- [x] 2.1 Implement normalized event schemas for `call_enter`, `call_exit`, `error`, `marker`, and `process_mem`
- [x] 2.2 Implement parent-child span linkage and root span handling in event emission
- [x] 2.3 Implement deterministic routing to entry-scoped streams and global fallback stream
- [x] 2.4 Implement session directory and file layout for entry event files and global event file

## 3. Incremental Analysis and Reporting

- [x] 3.1 Implement incremental analysis scheduler with timer (`T`), event threshold (`N`), and idle (`I`) triggers
- [x] 3.2 Implement immediate analysis trigger for critical error events
- [x] 3.3 Implement per-entry Chinese text report generation with call chain tree and error path sections
- [x] 3.4 Implement global Chinese error summary report generation with latest snapshot pointer and rolling retention (`K`)

## 4. Memory Observability and Runtime Controls

- [x] 4.1 Implement process memory sampling (`process_mem`) with RSS metrics
- [x] 4.2 Implement span entry/exit memory capture and delta computation fields
- [x] 4.3 Implement observability modes (`lite`, `enhanced`) and apply mode-specific default sampling behavior
- [x] 4.4 Implement feature toggles for process memory, span memory, chain memory reporting, and console memory display

## 5. Console Contract and Validation

- [x] 5.1 Implement terminal output formatter as `[time] [level] [function] message`
- [x] 5.2 Ensure report pipeline writes full reports to files only and avoids full terminal report dumps
- [x] 5.3 Add automated tests for nested entry routing, global fallback routing, and chain reconstruction correctness
- [x] 5.4 Add automated tests for incremental trigger behavior, memory signal emission, and output format constraints

## 6. Documentation and Readiness

- [x] 6.1 Document entry selection guidance and marker usage guidance for developers
- [x] 6.2 Document runtime overhead expectations and trade-offs for `lite` vs `enhanced` modes
- [x] 6.3 Document report file locations, snapshot lifecycle, and troubleshooting workflow
- [x] 6.4 Run end-to-end validation in a long-running multi-process sample and capture acceptance notes
