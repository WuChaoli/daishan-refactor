---
name: log-manager-observability
description: Implement, debug, and extend this project's Python runtime observability system. Use when tasks involve entry/trace decorators, event routing, incremental Chinese reports, memory telemetry, terminal output contract, or tests/docs under log_manager/, tests/, and docs/.
---

# Log Manager Observability

## Overview

Use this skill to work on the `log-manager` codebase end-to-end: instrumentation, event model, incremental reporting, memory signals, output formatting, and related tests/docs.

Prefer minimal, scoped edits and keep behavior aligned with OpenSpec artifacts in `openspec/changes/python-entry-global-log-observability/`.

## Workflow

1. Read current change context first:
   - `openspec/changes/python-entry-global-log-observability/proposal.md`
   - `openspec/changes/python-entry-global-log-observability/design.md`
   - `openspec/changes/python-entry-global-log-observability/specs/**/*.md`
   - `openspec/changes/python-entry-global-log-observability/tasks.md`
2. Implement only the required module(s); avoid broad refactors.
3. Keep output contracts stable:
   - Terminal: `[time] [level] [function] message`
   - Methods as `ClassName.func`, plain functions as `func`
   - Full reports written to files, not terminal dumps
4. Validate quickly:
   - `python -m compileall -q log_manager tests`
   - `python -m pytest -q` (if pytest is installed)
5. Update docs/tests when behavior changes:
   - `docs/usage.md`, `docs/operations.md`, `docs/validation.md`
   - `tests/test_routing.py`, `tests/test_reporting.py`, `tests/test_runtime_behavior.py`

## Project Map

Read `references/project-map.md` before non-trivial edits. It documents:

- module responsibilities in `log_manager/`
- runtime event/report path contracts
- trigger and memory behavior expectations
- recommended edit boundaries

## Guardrails

- Keep event field names backward compatible unless spec/design explicitly changed.
- Preserve directory layout under `.log-manager/runs/` and `.log-manager/reports/`.
- Prefer adding focused tests over manual-only verification.
- If task intent conflicts with OpenSpec artifacts, propose artifact update before coding.
