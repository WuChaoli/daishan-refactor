# Coding Conventions

**Analysis Date:** 2026-02-28

## Naming Patterns

**Files:**
- Predominantly `snake_case.py` for Python modules.
- Tests generally use `test_*.py` naming.
- Some historical naming debt exists (for example `source_dispath_srvice.py`).

**Functions/Variables:**
- Functions and variables mainly use snake_case.
- Constants/env keys use UPPER_SNAKE_CASE (`DIFY_BASE_RUL`, `RAGFLOW_API_KEY`).

**Types/Models:**
- Pydantic models use PascalCase (`ChatRequest`, `IntentResult`, `Settings`).
- Dataclasses are used for lightweight DTOs (`RetrievalResult`, `IntentRecognitionResult`).

## Code Style

**Formatting:**
- No single enforced formatter config found at root (no global `ruff`/`black`/`isort` config in root pyproject).
- Style is mostly PEP8-like with occasional long lines and mixed comment density.

**Linting:**
- Lint workflow is not centrally enforced in repository-level automation.

## Import Organization

**Observed Pattern:**
1. stdlib imports.
2. third-party imports.
3. internal imports (`from src...`).

**Monorepo-specific Pattern:**
- Several entrypoints and tests mutate `sys.path` at runtime (`src/rag_stream/main.py`, `src/rag_stream/tests/conftest.py`, `tests/conftest.py`).

## Error Handling

**Patterns:**
- API boundaries use `HTTPException` for invalid requests.
- Service boundaries often catch broad exceptions and degrade gracefully (return `[]` or fallback route).
- Logging of failures uses marker/logger before fallback.

**Tradeoff:**
- Broad `except Exception` keeps service alive but can hide root causes.

## Logging

**Framework:**
- `log-manager` marker/trace for rag_stream.
- `log_decorator` logger in Digital_human_command_interface.

**Patterns:**
- Structured marker events with small payload dicts.
- Key lifecycle points are instrumented (startup, query, dispatch, errors).

## Comments

**Usage:**
- Inline Chinese comments are common, especially around startup/config path decisions.
- Docstrings are widely used for service methods and route handlers.

## Function Design

**Observed style:**
- Service modules prefer many small helper functions (especially dispatch parsers and transformers).
- Business orchestration functions are async and delegate blocking calls with `asyncio.to_thread`.

## Module Design

**Patterns:**
- Clear module splits: `routes`, `services`, `models`, `utils`, `config`.
- Base-class template method used for intent pipeline (`BaseIntentService` -> `IntentService`).

**Deviations to watch:**
- Duplicate/overlapping logic across modules (for example JSON extraction helpers in multiple dispatch services).
- Mixed packaging standards across subprojects (`pyproject.toml` and `setup.py` coexist).

---

*Convention analysis: 2026-02-28*
*Update when linting/packaging standards are unified*
