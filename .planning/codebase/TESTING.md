# Testing Patterns

**Analysis Date:** 2026-02-28

## Test Framework

**Runner:**
- Pytest is the primary test runner.
- Local package-level pytest config exists in `src/log-manager/pyproject.toml`.

**Assertion Library:**
- Native `assert` style with pytest.
- Mocking via `unittest.mock` (`patch`, `AsyncMock`, `MagicMock`) is common.

**Run Commands:**
```bash
uv run pytest                                   # all tests
uv run pytest src/rag_stream/tests              # rag_stream suite
uv run pytest tests                             # root suite
uv run pytest test/2026-02-25_*                # archived task-specific tests
```

## Test File Organization

**Locations:**
- `tests/` for root-level regression and integration checks.
- `src/rag_stream/tests/` for service-domain tests.
- `src/log-manager/tests/` for log-manager package tests.
- `test/YYYY-MM-DD_<task>/` for archived task verifications.

**Naming:**
- Main pattern: `test_*.py`.
- Some ad-hoc scripts remain (for example `src/Digital_human_command_interface/test.py`).

## Test Structure

**Observed Pattern:**
- `pytest.fixture` for client/setup.
- `Test*` classes + `test_*` methods.
- API tests frequently validate status code families (`200/500`) when external dependencies are mocked or absent.

## Mocking

**Framework:**
- `unittest.mock.patch` and AsyncMock for external service paths.

**What is commonly mocked:**
- Environment variables via `patch.dict(os.environ, ...)`.
- SDK clients and async service calls.
- App state dependencies.

**What is less covered:**
- Full end-to-end flows against real external services (RAGFlow/Dify/SQL).

## Fixtures and Factories

**Fixtures:**
- `TestClient(app)` fixture pattern in API tests.
- `conftest.py` adjusts import paths for monorepo execution.

**Data Setup:**
- Inline request payloads are common.
- Task-specific regression tests are archived under dated folders.

## Coverage and Gaps

**Strengths:**
- Strong coverage in `src/rag_stream/tests/` around routing, intent handling, dispatch logic, and config compatibility.

**Gaps:**
- No unified repository coverage gate was detected.
- Multi-service integration contracts are only partially validated.
- Security and performance regression tests are limited.

## Practical Guidance

- Prefer adding tests adjacent to the changed subsystem (`src/rag_stream/tests/` or package-local tests).
- For cross-module regressions, add root `tests/` case and archive task proof under `test/YYYY-MM-DD_<task>/`.
- Mock external APIs by default unless validating integration behavior explicitly.

---

*Testing analysis: 2026-02-28*
*Update when test command/coverage policy changes*
