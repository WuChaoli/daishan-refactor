# External Integrations

**Analysis Date:** 2026-02-28

## APIs & External Services

**RAGFlow:**
- Used for intent retrieval and multi-dataset semantic matching.
  - Client: internal `ragflow_sdk` + adapter (`src/rag_stream/src/utils/ragflow_client.py`).
  - Auth: `RAGFLOW_API_KEY` / YAML `ragflow.api_key`.
  - Endpoints: configured by `ragflow.base_url` in `src/rag_stream/config.yaml`.

**Dify:**
- Used for chatflow, entity extraction, and dispatch reasoning.
  - Client: internal `dify_sdk` (`src/dify_sdk/`) and `DifyClientFactory` (`src/rag_stream/src/utils/dify_client_factory.py`).
  - Auth: `DIFY_CHAT_APIKEY_*` and legacy keys (`DIFY_CHAT_SQL_FORMATTER_KEY`, etc.).
  - Base URL: `DIFY_BASE_RUL` env variable (note typo in var name is intentional in current code).

**DaiShanSQL / SQL API bridge:**
- SQL generation and data query fallback path for Type2/Type3 flows.
  - Client path: `DaiShanSQL.Server` usage in `src/rag_stream/src/services/chat_general_service.py`.
  - HTTP bridge: `requests.post(self.api_url_ds, json={"sql": sql})` in `src/DaiShanSQL/DaiShanSQL/SQL/sql_utils.py`.

## Data Storage

**Databases:**
- Primary external data source appears to be an enterprise SQL/DM system accessed via API wrapper and SQL templates.
- Mapping and retrieval configuration is in YAML and JSON (`src/rag_stream/config.yaml`, `intent_mapping.example.json`).

**Files/Artifacts:**
- Session state is in memory (`src/rag_stream/src/utils/session_manager.py`), not persisted.
- Logs and run reports are file-based (`logs/`, `.log-manager/`).

## Authentication & Identity

**Service Auth:**
- API key pattern via `.env` variables for Dify/RAGFlow/OpenAI related services.
- No user auth middleware at FastAPI boundary in mapped services; endpoints are generally open internally.

## Monitoring & Observability

**Logging:**
- `log-manager` markers/traces are integrated in `rag_stream`.
- `log_decorator` is used in other modules (`Digital_human_command_interface`).

**Telemetry:**
- OpenTelemetry libs exist in root dependencies, but end-to-end pipeline wiring is partial/not centralized.

## CI/CD & Deployment

**Hosting/Runtime:**
- Service startup patterns documented via uvicorn/gunicorn commands in `src/rag_stream/README.md`.
- No `.github/workflows` found in repository root during scan.

## Environment Configuration

**Development:**
- `.env` for secrets, `config.yaml` for non-secret config.
- Multiple modules load their own `.env` by absolute/relative path.

**Production:**
- Environment separation is documented (`.env.development` / `.env.production` in `src/rag_stream/README.md`), but code still contains legacy `.env` loading behavior.

## Webhooks & Callbacks

- No explicit inbound webhook framework was identified in current FastAPI routes.
- SSE streaming is used for chat responses (`StreamingResponse` in `src/rag_stream/src/routes/chat_routes.py`).

---

*Integration audit: 2026-02-28*
*Update when service endpoints/auth models change*
