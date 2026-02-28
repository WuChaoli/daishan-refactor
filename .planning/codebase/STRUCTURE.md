# Codebase Structure

**Analysis Date:** 2026-02-28

## Directory Layout

```text
daishan-refactor/
├── src/                    # Core source code (services + internal SDKs)
├── tests/                  # Root-level regression tests
├── test/                   # Archived task-specific tests (dated folders)
├── docs/                   # Static docs + contexts + archive
├── openspec/               # Spec/change artifacts
├── scripts/                # Utility scripts
├── .codex/                 # Codex prompts/skills
├── .company/               # Company role/tool metadata
├── main.py                 # Root entry script (minimal)
├── pyproject.toml          # Root packaging/dependency metadata
├── requirements.txt        # Legacy dependency list
└── uv.lock                 # uv lockfile
```

## Directory Purposes

**`src/rag_stream/`:**
- Purpose: primary FastAPI service.
- Contains: `main.py`, `src/config`, `src/routes`, `src/services`, `src/utils`, tests, static assets.
- Key files: `src/rag_stream/main.py`, `src/rag_stream/src/routes/chat_routes.py`.

**`src/DaiShanSQL/`:**
- Purpose: SQL-oriented utilities and API adapters.
- Contains: package `DaiShanSQL/SQL` and `DaiShanSQL/Utils` modules.
- Key files: `src/DaiShanSQL/DaiShanSQL/SQL/sql_utils.py`, `src/DaiShanSQL/DaiShanSQL/api_server.py`.

**`src/Digital_human_command_interface/`:**
- Purpose: secondary intent/chat service.
- Contains: FastAPI entry, config, nested `src/` modules.

**`src/dify_sdk/` and `src/ragflow_sdk/`:**
- Purpose: internal SDK implementations for external LLM/retrieval platforms.

**`src/log-manager/` and `src/log_decorator/`:**
- Purpose: tracing/reporting/log decoration utilities used by services.

## Key File Locations

**Entry Points:**
- `main.py` - root script.
- `src/rag_stream/main.py` - main service runtime.
- `src/Digital_human_command_interface/main.py` - secondary service runtime.

**Configuration:**
- `pyproject.toml` - root dependency manifest.
- `src/rag_stream/config.yaml` - rag_stream non-secret settings.
- `src/Digital_human_command_interface/config.yaml` - digital-human service settings.
- `src/DaiShanSQL/DaiShanSQL/.env` - DaiShanSQL secret/env config.

**Core Logic:**
- `src/rag_stream/src/services/` - intent/chat/dispatch workflows.
- `src/rag_stream/src/models/` - request/response and domain models.
- `src/rag_stream/src/utils/` - external adapters and helpers.

**Testing:**
- `tests/` - cross-module and integration checks.
- `src/rag_stream/tests/` - service-level unit/integration tests.
- `src/log-manager/tests/` - package-specific tests.
- `test/YYYY-MM-DD_<task>/` - archived task tests.

## Naming Conventions

**Files:**
- Predominantly `snake_case.py`.
- Tests mostly `test_*.py`.
- Some legacy typo names exist, e.g. `source_dispath_srvice.py`.

**Directories:**
- Feature or package oriented (for example `services`, `models`, `utils`).
- Mixed style in monorepo subprojects due to incremental migration.

## Where to Add New Code

**New rag_stream feature:**
- Implementation: `src/rag_stream/src/services/`.
- API route: `src/rag_stream/src/routes/`.
- Schema/model: `src/rag_stream/src/models/`.
- Tests: `src/rag_stream/tests/` plus `test/YYYY-MM-DD_<task>/` archive when task closes.

**New shared SDK behavior:**
- Dify integration: `src/dify_sdk/`.
- RAGFlow integration: `src/ragflow_sdk/`.

**New documentation/context:**
- Static docs: `docs/static/`.
- Active context: `docs/contexts/<context-id>/`.

## Special Directories

**`.planning/`:**
- Purpose: GSD planning artifacts (including this codebase map).
- Source: generated/maintained during planning workflows.
- Committed: yes, when used as project context.

**`.worktrees/`:**
- Purpose: isolated development worktrees.
- Usually not committed in main history.

---

*Structure analysis: 2026-02-28*
*Update when top-level layout changes materially*
