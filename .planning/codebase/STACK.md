# Technology Stack

**Analysis Date:** 2026-02-28

## Languages

**Primary:**
- Python 3.12+ - Main runtime for top-level project (`pyproject.toml`).

**Secondary:**
- Python 3.10+ - `log-manager` subpackage (`src/log-manager/pyproject.toml`).
- Markdown/YAML/TOML - Docs, configuration, and packaging metadata.

## Runtime

**Environment:**
- ASGI runtime with `uvicorn` for FastAPI services.
- Async + sync mixed execution (`asyncio`, `httpx`, `requests`, SDK wrappers).

**Package Manager:**
- `uv` is the intended dependency manager (project governance + `uv.lock`).
- Legacy `requirements.txt` files also exist (`requirements.txt`, `src/rag_stream/requirements.txt`).

## Frameworks

**Core:**
- FastAPI (`main API services in `src/rag_stream/main.py` and `src/Digital_human_command_interface/main.py`).
- Pydantic v2 models (`src/rag_stream/src/models/schemas.py`, `src/rag_stream/src/config/settings.py`).

**Testing:**
- Pytest as the primary runner (`tests/`, `src/rag_stream/tests/`, `src/log-manager/tests/`).
- `fastapi.testclient` for API-level tests.

**Build/Dev:**
- Setuptools packaging for internal SDK/modules (`src/dify_sdk/setup.py`, `src/ragflow_sdk/setup.py`, `src/log-manager/pyproject.toml`).
- Uvicorn for local service startup.

## Key Dependencies

**Critical:**
- `fastapi` - HTTP API surface for chat/dispatch services.
- `pydantic` and `pydantic-settings` - request/config modeling.
- `aiohttp`/`httpx`/`requests` - external HTTP integrations.
- `openai` - LLM-related integration used by DaiShanSQL path.
- `PyYAML` - YAML-driven configuration loading.

**Infrastructure/Internal SDKs:**
- `ragflow_sdk` - RAG retrieval and dataset APIs (`src/ragflow_sdk/`).
- `dify_sdk` - Dify chat workflow integration (`src/dify_sdk/`).
- `DaiShanSQL` - SQL generation and fixed-query utilities (`src/DaiShanSQL/`).
- `log-manager` / `log_decorator` - instrumentation and structured logs (`src/log-manager/`, `src/log_decorator/`).

## Configuration

**Environment:**
- Sensitive settings are loaded from `.env` (for example `src/rag_stream/main.py`, `src/DaiShanSQL/DaiShanSQL/__init__.py`).
- Non-sensitive service settings are loaded from YAML (`src/rag_stream/config.yaml`, `src/Digital_human_command_interface/config.yaml`).
- `settings` object merges YAML + env override (`src/rag_stream/src/config/settings.py`).

**Build/Packaging:**
- Root packaging: `pyproject.toml` + `uv.lock`.
- Submodule packaging: multiple `setup.py` / `pyproject.toml` files.

## Platform Requirements

**Development:**
- Linux/macOS shell environment with Python and `uv`.
- Local access to configured RAGFlow/Dify endpoints for integration tests.

**Production:**
- ASGI deployment (`uvicorn`/`gunicorn+uvicorn` style documented in `src/rag_stream/README.md`).
- External services required: RAGFlow, Dify, SQL endpoint/OpenAI-backed SQL pipeline.

---

*Stack analysis: 2026-02-28*
*Update after dependency/runtime policy changes*
