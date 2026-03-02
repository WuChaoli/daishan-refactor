---
type: quick-summary
task: 3
description: 更新打包docker镜像
date: 2026-03-02
status: partial
---

## What Changed

1. Updated `src/rag_stream/Dockerfile`:
- Switched editable dependency install from `pip` to `uv pip install --system -e .`
- Added `UV_SYSTEM_PYTHON=1` for uv-based system installs in builder stage
- Added `APP_ENV` build arg and propagated it into runtime env for build-time environment alignment

2. Updated `src/rag_stream/docker-compose.yml`:
- Added explicit image name: `${RAG_STREAM_IMAGE:-daishan/rag_stream:local}`
- Unified build entry with `target: runtime`
- Added build arg passthrough: `APP_ENV: ${APP_ENV:-development}`
- Made `env_file` optional for both `rag_stream` and `digital_human` to allow config rendering in environments without root `.env`

3. Updated `src/rag_stream/docker-compose.prod.yml`:
- Fixed invalid compose schema placement by moving `restart_policy` from `deploy.resources` to `deploy`

## Verification

1. Compose render check:
- Command:
  `docker compose -f src/rag_stream/docker-compose.yml -f src/rag_stream/docker-compose.prod.yml config >/tmp/rag_stream.compose.rendered.yml && test -s /tmp/rag_stream.compose.rendered.yml`
- Result: PASS (`compose-config-ok`)

2. Build and runtime health chain:
- Command:
  `docker compose -f src/rag_stream/docker-compose.yml -f src/rag_stream/docker-compose.prod.yml build rag_stream && docker compose -f src/rag_stream/docker-compose.yml -f src/rag_stream/docker-compose.prod.yml up -d rag_stream && docker compose -f src/rag_stream/docker-compose.yml -f src/rag_stream/docker-compose.prod.yml exec -T rag_stream python -c "import urllib.request; urllib.request.urlopen('http://localhost:11028/health', timeout=5); print('health-ok')"`
- Result: FAIL (build stage blocked by network access to Docker Hub)
- Key error:
  `failed to do request: Head "https://registry-1.docker.io/v2/library/python/manifests/3.12-slim-bookworm": ... connect: connection refused`

## Commits

- `f28588c` feat(quick-3): align rag_stream docker build and image packaging

## Risks / Blockers

- Current environment cannot reach Docker image registries (`docker.io` / `ghcr.io` metadata pull), so end-to-end container startup and `/health` verification could not be completed.
- After registry/network access is restored, rerun the build+up+health command chain to finish runtime proof.
