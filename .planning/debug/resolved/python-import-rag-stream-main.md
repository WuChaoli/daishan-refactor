---
status: resolved
trigger: "python-import-rag-stream-main"
created: 2026-02-28
updated: 2026-02-28
---

## Current Focus

hypothesis: The editable package installation had the wrong path mapping, and there were incorrect `src.` imports in the code

test: Reinstall package and fix incorrect imports

expecting: Program starts successfully without import errors

next_action: Mark as resolved

## Symptoms

expected: Python program should start normally without import errors
actual: Program crashes immediately with ModuleNotFoundError
errors: |
  Traceback (most recent call last):
    File "/home/wuchaoli/codespace/daishan-refactor/src/rag_stream/main.py", line 1, in <module>
      from rag_stream.main import app
  ModuleNotFoundError: No module named 'rag_stream.main'
reproduction: Run `/home/wuchaoli/codespace/daishan-refactor/.venv/bin/python /home/wuchaoli/codespace/daishan-refactor/src/rag_stream/main.py`
timeline: Unknown - first time encountering this issue

## Eliminated

- hypothesis: Package not installed in venv
  evidence: Package is installed as editable (__editable__.rag_stream-0.1.0.pth exists)
  timestamp: 2026-02-28

- hypothesis: Wrong Python executable
  evidence: Python path shows correct venv and editable hooks are registered
  timestamp: 2026-02-28

- hypothesis: Entry point file has wrong imports
  evidence: The entry point imports were correct; the issue was the editable package path and incorrect `src.` imports in other files
  timestamp: 2026-02-28

## Evidence

- timestamp: 2026-02-28
  checked: Package structure and pyproject.toml
  found: |
    - src/rag_stream/main.py (entry point) imports: from rag_stream.main import app
    - src/rag_stream/src/main.py (actual app) defines: app = FastAPI(...)
    - pyproject.toml has: package-dir = { rag_stream = "src" }
    - The editable package hook was registered but with wrong path
  implication: The editable installation had stale/incorrect path mapping

- timestamp: 2026-02-28
  checked: Editable finder file
  found: MAPPING showed incorrect path: '/home/wuchaoli/codespace/daishan-refactor/src/rag_stream/rag_stream' instead of '/home/wuchaoli/codespace/daishan-refactor/src/rag_stream/src'
  implication: Package was installed with wrong directory mapping

- timestamp: 2026-02-28
  checked: Code for incorrect imports
  found: Multiple files used `from src.` instead of `from rag_stream.`:
    - src/rag_stream/src/utils/intent_classifier.py
    - src/rag_stream/src/utils/query_chat.py
    - src/rag_stream/src/services/intent_service/intent_service.py
  implication: These imports would fail even after fixing the editable package

## Resolution

root_cause: |
  Two issues:
  1. The editable package installation had stale path mapping pointing to non-existent directory
  2. Multiple source files used incorrect `from src.` imports instead of `from rag_stream.`

fix: |
  1. Reinstalled rag-stream package in editable mode: `uv pip install -e src/rag_stream`
  2. Fixed imports in 3 files to use `rag_stream.` instead of `src.`:
     - src/rag_stream/src/utils/intent_classifier.py
     - src/rag_stream/src/utils/query_chat.py
     - src/rag_stream/src/services/intent_service/intent_service.py

verification: |
  Ran: timeout 5 .venv/bin/python src/rag_stream/main.py
  Result: Server started successfully, no import errors
  Output: "Uvicorn running on http://0.0.0.0:11028"

files_changed:
  - src/rag_stream/src/utils/intent_classifier.py (fixed imports)
  - src/rag_stream/src/utils/query_chat.py (fixed imports)
  - src/rag_stream/src/services/intent_service/intent_service.py (fixed imports)
