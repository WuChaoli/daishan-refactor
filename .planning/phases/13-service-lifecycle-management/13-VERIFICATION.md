---
phase: 13-service-lifecycle-management
verified: 2026-03-01T15:00:00Z
status: gaps_found
score: 2/5 must-haves verified
gaps:
  - truth: "Database connections released during shutdown"
    status: failed
    reason: "Import broken - rag_stream.shutdown module not found"
    artifacts:
      - path: "src/rag_stream/shutdown.py"
        issue: "File exists at wrong location (outside Python package)"
      - path: "src/rag_stream/src/main.py"
        issue: "Cannot import rag_stream.lifespan - ModuleNotFoundError"
    missing:
      - "Move shutdown.py to src/rag_stream/src/shutdown.py (inside package)"
      - "Update pyproject.toml packages list to include rag_stream.shutdown"
  - truth: "HTTP client connection pool closed gracefully"
    status: failed
    reason: "Import broken - rag_stream.shutdown module not found"
    artifacts:
      - path: "src/rag_stream/shutdown.py"
        issue: "File exists at wrong location (outside Python package)"
    missing:
      - "Move shutdown.py to src/rag_stream/src/shutdown.py (inside package)"
  - truth: "Service responds to SIGTERM with proper cleanup logging"
    status: partial
    reason: "Signal handlers exist in main.py but lifespan module cannot be imported"
    artifacts:
      - path: "src/rag_stream/lifespan.py"
        issue: "File exists at wrong location (outside Python package)"
      - path: "src/rag_stream/startup.py"
        issue: "File exists at wrong location (outside Python package)"
    missing:
      - "Move lifespan.py, startup.py, shutdown.py to src/rag_stream/src/ directory"
      - "Update pyproject.toml packages list to include new modules"
      - "Update imports in lifespan.py from 'rag_stream.xxx' to relative imports"
---

# Phase 13: Service Lifecycle Management Verification Report

**Phase Goal:** 启动关闭与资源清理
**Verified:** 2026-03-01T15:00:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth | Status | Evidence |
| --- | ------- | ---------- | -------------- |
| 1 | Service responds to SIGTERM with proper cleanup logging | ⚠️ PARTIAL | Signal handlers exist in main.py (lines 171-198), but lifespan import fails |
| 2 | Database connections released during shutdown | ✗ FAILED | shutdown.py exists but at wrong location; import `rag_stream.shutdown` fails |
| 3 | HTTP client connection pool closed gracefully | ✗ FAILED | shutdown.py exists but at wrong location; import `rag_stream.shutdown` fails |
| 4 | Uvicorn configured with 4 workers and 30s graceful timeout | ✓ VERIFIED | Dockerfile line 97: `--workers 4 --timeout-keep-alive 30 --timeout-graceful-shutdown 30` |
| 5 | Docker stop_grace_period matches Uvicorn timeout | ✓ VERIFIED | docker-compose.yml lines 45-46, 99-100: `stop_signal: SIGTERM`, `stop_grace_period: 30s` |

**Score:** 2/5 truths verified

### Root Cause Analysis

**Critical Structural Issue:** The lifecycle modules (`lifespan.py`, `startup.py`, `shutdown.py`) were created at `src/rag_stream/` level instead of inside the Python package at `src/rag_stream/src/`.

**Impact:**
- `pyproject.toml` maps `rag_stream` package to `src/` directory via `package-dir = { rag_stream = "src" }`
- Files at `src/rag_stream/*.py` are NOT part of the `rag_stream` Python package
- main.py imports `from rag_stream.lifespan import lifespan` fails with `ModuleNotFoundError: No module named 'rag_stream.lifespan'`
- **The service cannot start** due to import errors

**Verification Evidence:**
```bash
$ .venv/bin/python -c "from rag_stream.lifespan import lifespan"
ModuleNotFoundError: No module named 'rag_stream.lifespan'

$ .venv/bin/python -c "from rag_stream.startup import init_database"
ModuleNotFoundError: No module named 'rag_stream.startup'

$ .venv/bin/python -c "from rag_stream.shutdown import close_database"
ModuleNotFoundError: No module named 'rag_stream.shutdown'
```

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | ----------- | ------ | ------- |
| `src/rag_stream/lifespan.py` | Lifespan context manager | ⚠️ ORPHANED | File exists at wrong location; not importable as `rag_stream.lifespan` |
| `src/rag_stream/startup.py` | Initialization utilities | ⚠️ ORPHANED | File exists at wrong location; not importable as `rag_stream.startup` |
| `src/rag_stream/shutdown.py` | Cleanup utilities | ⚠️ ORPHANED | File exists at wrong location; not importable as `rag_stream.shutdown` |
| `src/rag_stream/src/main.py` | FastAPI app with lifespan | ✗ BROKEN | Import `from rag_stream.lifespan` fails |
| `src/rag_stream/docker-compose.yml` | Container stop configuration | ✓ VERIFIED | stop_grace_period: 30s, stop_signal: SIGTERM |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| main.py | lifespan.py | `from rag_stream.lifespan import lifespan` | ✗ NOT_WIRED | ModuleNotFoundError |
| lifespan.py | startup.py | `from rag_stream.startup import ...` | ✗ NOT_WIRED | Parent module not importable |
| lifespan.py | shutdown.py | `from rag_stream.shutdown import ...` | ✗ NOT_WIRED | Parent module not importable |
| docker-compose.yml | lifespan.py | timeout alignment | ⚠️ PARTIAL | Config correct but lifespan broken |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| LIFECYCLE-01 | 13-01-PLAN | 服务启动脚本（支持 graceful startup） | ✗ BLOCKED | Code exists but imports broken - service cannot start |
| LIFECYCLE-02 | 13-01-PLAN | 优雅关闭机制（graceful shutdown） | ✗ BLOCKED | Code exists but imports broken - service cannot start |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| startup.py | 63 | "This is a placeholder for database initialization" | ℹ️ Info | Documented as intentional - DB accessed via RAGFlow |
| shutdown.py | 43 | "This is a placeholder for database cleanup" | ℹ️ Info | Documented as intentional - DB accessed via RAGFlow |

### Human Verification Required

None - the critical import failure is programmatically verifiable and blocks all functionality.

### Gaps Summary

**Critical Gap: Module Location Mismatch**

The phase created three new modules (`lifespan.py`, `startup.py`, `shutdown.py`) at the project root level (`src/rag_stream/`) instead of inside the Python package (`src/rag_stream/src/`). This structural error causes all imports to fail:

1. **Files at wrong location:**
   - Current: `src/rag_stream/lifespan.py`
   - Expected: `src/rag_stream/src/lifespan.py` (inside package)

2. **Import chain broken:**
   - main.py → `from rag_stream.lifespan import lifespan` → **FAILS**
   - lifespan.py → `from rag_stream.startup import ...` → **FAILS**
   - startup.py → `from rag_stream.config.settings import settings` → Works (config is in package)

3. **Service cannot start:**
   ```python
   # main.py line 21
   from rag_stream.lifespan import lifespan as modular_lifespan
   # ModuleNotFoundError: No module named 'rag_stream.lifespan'
   ```

**What works:**
- Docker configuration (stop_grace_period, stop_signal)
- Uvicorn configuration (workers, timeouts)
- Signal handlers in main.py
- Logging structure in lifecycle modules

**What's blocked:**
- Service startup (import error)
- Graceful shutdown (lifespan not loaded)
- Database/HTTP cleanup (shutdown module not loaded)

### Remediation Required

1. **Move files to correct location:**
   ```bash
   mv src/rag_stream/lifespan.py src/rag_stream/src/lifespan.py
   mv src/rag_stream/startup.py src/rag_stream/src/startup.py
   mv src/rag_stream/shutdown.py src/rag_stream/src/shutdown.py
   ```

2. **Update pyproject.toml packages list:**
   ```toml
   packages = [
       "rag_stream",
       "rag_stream.config",
       "rag_stream.lifespan",    # Add
       "rag_stream.startup",     # Add
       "rag_stream.shutdown",    # Add
       ...
   ]
   ```

3. **Update imports in lifespan.py to relative imports:**
   ```python
   # Change from:
   from rag_stream.shutdown import close_database, close_http_client
   from rag_stream.startup import init_database, init_http_client, wait_for_external_services
   
   # To:
   from .shutdown import close_database, close_http_client
   from .startup import init_database, init_http_client, wait_for_external_services
   ```

4. **Verify imports work:**
   ```bash
   python -c "from rag_stream.lifespan import lifespan; print('OK')"
   ```

---

_Verified: 2026-03-01T15:00:00Z_
_Verifier: Claude (gsd-verifier)_
