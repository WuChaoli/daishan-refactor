#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

IMAGE_NAME="${RAG_STREAM_IMAGE:-daishan/rag_stream:local}"
IMAGE_TAR_PATH="${RAG_STREAM_IMAGE_TAR:-${SCRIPT_DIR}/rag_stream_local.tar}"
CONTAINER_NAME="${RAG_STREAM_CONTAINER:-rag_stream}"
HOST_PORT="${RAG_STREAM_HOST_PORT:-11027}"
CONTAINER_PORT="${RAG_STREAM_CONTAINER_PORT:-11027}"
ENV_FILE="${RAG_STREAM_ENV_FILE:-${PROJECT_ROOT}/src/Digital_human_command_interface/.env}"
CONFIG_FILE="${RAG_STREAM_CONFIG_FILE:-${PROJECT_ROOT}/src/rag_stream/config.yaml}"
HEALTH_CHECK_TIMEOUT_SECONDS="${RAG_STREAM_HEALTH_TIMEOUT:-60}"

HEALTH_URL="http://127.0.0.1:${HOST_PORT}/health"
CATEGORIES_URL="http://127.0.0.1:${HOST_PORT}/api/categories"

log() {
  printf '[rag_stream] %s\n' "$*"
}

fail() {
  printf '[rag_stream][error] %s\n' "$*" >&2
  exit 1
}

check_command() {
  command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"
}

check_port_conflict() {
  local port_owners
  port_owners="$(docker ps --filter "publish=${HOST_PORT}" --format '{{.Names}}')"
  if [[ -z "${port_owners}" ]]; then
    return 0
  fi

  while IFS= read -r owner; do
    [[ -z "${owner}" ]] && continue
    if [[ "${owner}" != "${CONTAINER_NAME}" ]]; then
      fail "Host port ${HOST_PORT} is already used by container '${owner}'. Stop it first, then retry."
    fi
  done <<< "${port_owners}"
}

load_image_from_tar() {
  [[ -f "${IMAGE_TAR_PATH}" ]] || fail "Image tar not found: ${IMAGE_TAR_PATH}"
  log "Loading image from tar: ${IMAGE_TAR_PATH}"
  docker load -i "${IMAGE_TAR_PATH}" >/dev/null
}

ensure_image_available() {
  load_image_from_tar
  docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1 || \
    fail "Image '${IMAGE_NAME}' not found after docker load. Check image tag inside tar package."
}

remove_existing_container() {
  if docker ps -a --format '{{.Names}}' | grep -Fx "${CONTAINER_NAME}" >/dev/null 2>&1; then
    log "Removing existing container '${CONTAINER_NAME}'..."
    docker rm -f "${CONTAINER_NAME}" >/dev/null
  fi
}

wait_for_health() {
  local elapsed=0
  local code
  local body

  while (( elapsed < HEALTH_CHECK_TIMEOUT_SECONDS )); do
    code="$(curl -sS -o /tmp/rag_stream_health_body.txt -w '%{http_code}' "${HEALTH_URL}" || true)"
    body="$(cat /tmp/rag_stream_health_body.txt 2>/dev/null || true)"
    if [[ "${code}" == "200" ]] && [[ "${body}" == *'"status":"ok"'* ]]; then
      log "Health check passed: ${body}"
      return 0
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done

  log "Container logs (tail 120):"
  docker logs --tail 120 "${CONTAINER_NAME}" || true
  fail "Health check failed after ${HEALTH_CHECK_TIMEOUT_SECONDS}s. URL=${HEALTH_URL}"
}

verify_api_categories() {
  local code
  local body
  code="$(curl -sS -o /tmp/rag_stream_categories_body.txt -w '%{http_code}' "${CATEGORIES_URL}" || true)"
  body="$(cat /tmp/rag_stream_categories_body.txt 2>/dev/null || true)"

  if [[ "${code}" != "200" ]]; then
    fail "API verification failed. GET /api/categories returned HTTP ${code}. Body=${body}"
  fi
  if [[ "${body}" != *'"code":0'* ]]; then
    fail "API verification failed. Response body does not contain success code. Body=${body}"
  fi

  log "API verification passed: GET /api/categories returned success."
}

main() {
  check_command docker
  check_command curl

  [[ -f "${ENV_FILE}" ]] || fail "Env file not found: ${ENV_FILE}"
  [[ -f "${CONFIG_FILE}" ]] || fail "Config file not found: ${CONFIG_FILE}"

  ensure_image_available

  check_port_conflict
  remove_existing_container

  log "Starting container '${CONTAINER_NAME}' from image '${IMAGE_NAME}' on port ${HOST_PORT}..."
  docker run -d \
    --name "${CONTAINER_NAME}" \
    -p "${HOST_PORT}:${CONTAINER_PORT}" \
    --env-file "${ENV_FILE}" \
    -e LOG_CONSOLE_OUTPUT=true \
    -v "${CONFIG_FILE}:/app/src/rag_stream/config.yaml:ro" \
    "${IMAGE_NAME}" >/dev/null

  wait_for_health
  verify_api_categories

  log "All checks passed."
  log "Service URL: http://127.0.0.1:${HOST_PORT}"
}

main "$@"
