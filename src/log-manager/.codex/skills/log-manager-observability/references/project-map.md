# Project Map

## Code Modules

- `log_manager/config.py`
  - Runtime config model (`mode`, memory/report/console switches, base directory, session id).
- `log_manager/context.py`
  - Entry stack + span stack context management.
  - `session_id`, per-process `run_id`, trace/span id generation.
- `log_manager/decorators.py`
  - Public decorators: `entry_trace`, `trace` (sync + async wrappers).
- `log_manager/runtime.py`
  - Core runtime orchestration:
    - emit events
    - route entry/global streams
    - memory sampler thread
    - incremental trigger loop
    - marker emission
- `log_manager/storage.py`
  - JSONL append and storage path layout.
- `log_manager/reporting.py`
  - Entry report + global summary generation (Chinese text output).
- `log_manager/console.py`
  - Terminal line format contract.
- `log_manager/memory.py`
  - RSS collection (`psutil` if available, `/proc` fallback).
- `log_manager/__init__.py`
  - Public API export and `marker()` helper.

## Test Modules

- `tests/test_routing.py`
  - Nested entry routing and global fallback behavior.
- `tests/test_reporting.py`
  - Call chain and error path report assertions.
- `tests/test_runtime_behavior.py`
  - Trigger behavior, memory events, terminal format checks.
- `tests/conftest.py`
  - Runtime factory fixture.

## Runtime Output Contracts

- Event files:
  - `runs/<session>/entries/<entry_id>.events.jsonl`
  - `runs/<session>/global.events.jsonl`
- Report files:
  - `reports/<session>/entries/<entry_id>/latest.txt`
  - `reports/<session>/global-error-summary/latest.txt`

## Trigger Contracts

- Timer trigger (`trigger_timer_s`)
- Event threshold trigger (`trigger_event_count`)
- Idle trigger (`trigger_idle_s`)
- Immediate trigger on critical error (`immediate_on_error`)

## Safe Edit Boundaries

- Add new event fields only when corresponding report/tests are updated.
- Keep old fields intact unless a spec explicitly removes them.
- Avoid changing path conventions without updating docs + tests + migration notes.
