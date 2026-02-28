# Architecture

**Analysis Date:** 2026-02-28

## Pattern Overview

**Overall:** Python monorepo with multiple service entry points + internal SDK packages.

**Key Characteristics:**
- API-first service style (FastAPI + SSE streaming).
- Domain-oriented service split (`rag_stream`, `Digital_human_command_interface`, `DaiShanSQL`).
- Shared internal libraries under `src/` (RAGFlow SDK, Dify SDK, logging packages).
- Runtime wiring via environment variables and YAML configuration.

## Layers

**API Layer:**
- Purpose: expose HTTP endpoints and stream responses.
- Contains: FastAPI apps and route handlers.
- Locations: `src/rag_stream/main.py`, `src/rag_stream/src/routes/chat_routes.py`, `src/Digital_human_command_interface/main.py`.

**Service Layer:**
- Purpose: business orchestration for intent routing, dispatch, and response shaping.
- Contains: intent, chat-general, personnel/source dispatch, question suggestion flows.
- Locations: `src/rag_stream/src/services/`.

**Integration Layer:**
- Purpose: communicate with external platforms (RAGFlow, Dify, SQL/OpenAI path).
- Contains: adapters/factories and SDK wrappers.
- Locations: `src/rag_stream/src/utils/ragflow_client.py`, `src/rag_stream/src/utils/dify_client_factory.py`, `src/dify_sdk/`, `src/ragflow_sdk/`, `src/DaiShanSQL/`.

**Config/Model Layer:**
- Purpose: schema validation and config loading.
- Contains: Pydantic models, YAML/env loaders, request/response schemas.
- Locations: `src/rag_stream/src/config/settings.py`, `src/rag_stream/src/models/schemas.py`.

## Data Flow

**General Chat Flow (`/api/general`):**
1. Request enters `chat_routes.chat_general`.
2. Route delegates to `handle_chat_general`.
3. Intent service retrieves candidates from RAGFlow and classifies type.
4. Type-specific post-processing may call DaiShanSQL or Dify.
5. Route falls back to category chat and returns SSE stream.

**Dispatch Flow (`/ipark-ae/*-dispatch`):**
1. Request enters route handler.
2. Service extracts entities/intents using Dify.
3. Optional SQL lookup is performed for事故上下文.
4. Entities/resources are mapped, sorted, and returned as JSON list.

**State Management:**
- Session cache is in-memory (`SessionManager`), TTL-based cleanup, no durable backing store.

## Key Abstractions

**Intent Recognition Pipeline:**
- Base abstraction: `BaseIntentService` template method.
- Concrete behavior: `IntentService` with domain-specific priority logic.

**External Client Adapters:**
- `RagflowClient` wraps SDK retrieval behavior and similarity parsing.
- `DifyClientFactory` lazily instantiates named Dify clients from env.

## Entry Points

**Root Script:**
- `main.py` (placeholder hello-world entry).

**Main Service Entry:**
- `src/rag_stream/main.py` (primary chat/intent/dispatch service).

**Secondary Service Entry:**
- `src/Digital_human_command_interface/main.py` (parallel FastAPI service with overlapping domain).

## Error Handling

**Strategy:**
- Most service boundaries catch `ValueError`/`KeyError`/`Exception` and degrade to empty list or fallback route.
- API layer raises `HTTPException` for validation/business boundary failures.

## Cross-Cutting Concerns

**Logging:**
- Marker/trace instrumentation in core flows (`log-manager` integration).

**Validation:**
- Pydantic request schemas and config validators are used heavily in `rag_stream`.

**Security/CORS:**
- CORS allows `*` in service defaults; production hardening not enforced in code.

---

*Architecture analysis: 2026-02-28*
*Update after major flow/layer refactors*
