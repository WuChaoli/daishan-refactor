---
phase: 08-api-general
plan: 01
type: execute
subsystem: testing
tags: [e2e, api-testing, intent-classification, streaming]
dependency_graph:
  requires: []
  provides: [TEST-05]
  affects: []
tech_stack:
  added: [pandas, openpyxl, httpx]
  patterns: [excel-test-data, sse-stream-testing, server-lifecycle-management]
key_files:
  created:
    - src/rag_stream/tests/data/intent_test_cases.xlsx
    - src/rag_stream/tests/test_api_general_e2e.py
    - src/rag_stream/tests/README.md
  modified:
    - src/rag_stream/tests/conftest.py
    - pyproject.toml (dev dependencies)
decisions:
  - Excel format chosen for non-technical test case maintenance
  - Server lifecycle managed within test script for isolation
  - Async httpx used for SSE stream handling
  - SKIP_E2E_TEST env var for CI/CD flexibility
metrics:
  duration_minutes: 25
  tasks_completed: 3
  test_cases_created: 9
  files_created: 3
  files_modified: 1
---

# Phase 08 Plan 01: API General E2E Testing Summary

**One-liner:** Created end-to-end testing framework for `/api/general` with Excel-based test cases and automated server lifecycle management.

## What Was Built

### 1. Excel Test Dataset (`src/rag_stream/tests/data/intent_test_cases.xlsx`)

Created 9 test cases covering all 3 intent classification types:

| Type | Category | Count | Examples |
|------|----------|-------|----------|
| 1 | 岱山-指令集 | 3 | "园区安全态势如何？", "危化品企业有哪些？" |
| 2 | 岱山-数据库问题 | 3 | "XX企业的危化品类目是什么？" |
| 3 | 岱山-指令集-固定问题 | 3 | "东区的安全负责人是谁？" |

**Columns:** question, expected_type, description, notes

### 2. E2E Test Script (`src/rag_stream/tests/test_api_general_e2e.py`)

Complete testing framework with:

- **ServerManager**: Lifecycle management (start, health check, stop)
- **TestCase loading**: From Excel with optional type filtering
- **API calling**: Async httpx with SSE stream handling
- **Log parsing**: Intent classification result extraction from `.log-manager/runs/`
- **Report generation**: Console output + JSON file

**Key classes:**
- `ServerManager`: Uvicorn process management with SIGTERM/SIGKILL cleanup
- `TestCase` / `TestResult` / `TestReport`: Structured data classes
- `load_test_cases()`: Excel reader with pandas
- `parse_intent_classification_logs()`: Log marker parser

### 3. Test Helpers (`src/rag_stream/tests/conftest.py`)

Added:
- `E2EConfig`: Centralized configuration (timeout, URLs)
- `check_e2e_dependencies()`: Validation for pandas, openpyxl, httpx
- `get_dependency_install_hint()`: Setup guidance

### 4. Documentation (`src/rag_stream/tests/README.md`)

Comprehensive guide covering:
- 3 ways to run tests
- How to add new test cases
- Intent type reference table
- Output format documentation
- Helper function examples
- Troubleshooting section

## Execution Log

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Create Excel test dataset | `80c3332` |
| 2 | Implement E2E test script | `1eda076` |
| 3 | Add test helpers and docs | `419e5bf` |

## Dependencies Added

```toml
[dependency-groups]
dev = [
    "pandas>=3.0.1",
    "openpyxl>=3.1.5",
    "httpx>=0.28.1",  # already present
]
```

## Usage

```bash
# Run E2E tests
cd src/rag_stream
python tests/test_api_general_e2e.py

# Skip tests (for CI)
export SKIP_E2E_TEST=1

# Load test cases programmatically
from tests.test_api_general_e2e import load_test_cases
cases = load_test_cases(filter_type=1)  # Type1 only
```

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check

- [x] `src/rag_stream/tests/data/intent_test_cases.xlsx` exists with 9 test cases
- [x] `src/rag_stream/tests/test_api_general_e2e.py` exists and is importable
- [x] `src/rag_stream/tests/conftest.py` has E2EConfig and dependency checkers
- [x] `src/rag_stream/tests/README.md` has complete documentation
- [x] All commits created with proper messages

## Self-Check: PASSED
