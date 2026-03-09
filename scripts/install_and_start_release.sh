#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PYTHON_VERSION="${PYTHON_VERSION:-3.12}"
APP_MODULE="${APP_MODULE:-rag_stream.main}"
SERVICE_PORT="${SERVICE_PORT:-11027}"
HEALTH_TIMEOUT_SECONDS="${HEALTH_TIMEOUT_SECONDS:-60}"
LOG_DIR="${LOG_DIR:-${PACKAGE_ROOT}/logs}"
PID_FILE="${PID_FILE:-${LOG_DIR}/rag_stream.pid}"
RUN_LOG_FILE="${RUN_LOG_FILE:-${LOG_DIR}/rag_stream.out.log}"
ENV_FILE="${ENV_FILE:-${PACKAGE_ROOT}/.env.production}"

log() {
  printf '[release] %s\n' "$*"
}

fail() {
  printf '[release][error] %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"
}

load_env_file_if_exists() {
  if [[ -f "${ENV_FILE}" ]]; then
    # shellcheck disable=SC1090
    set -a && source "${ENV_FILE}" && set +a
    log "Loaded env file: ${ENV_FILE}"
  else
    log "Env file not found, continue with current process env: ${ENV_FILE}"
  fi
}

ensure_venv_and_dependencies() {
  if [[ ! -d "${PACKAGE_ROOT}/.venv" ]]; then
    log "Creating virtual environment with Python ${PYTHON_VERSION}"
    uv venv --python "${PYTHON_VERSION}" "${PACKAGE_ROOT}/.venv"
  fi

  log "Installing dependencies with uv lock"
  (
    cd "${PACKAGE_ROOT}"
    uv sync --frozen
  )
}

ensure_not_running() {
  if [[ -f "${PID_FILE}" ]]; then
    local old_pid
    old_pid="$(cat "${PID_FILE}" 2>/dev/null || true)"
    if [[ -n "${old_pid}" ]] && kill -0 "${old_pid}" 2>/dev/null; then
      fail "Service already running (pid=${old_pid}). Stop it first."
    fi
    rm -f "${PID_FILE}"
  fi
}

start_service() {
  mkdir -p "${LOG_DIR}"

  (
    cd "${PACKAGE_ROOT}"
    nohup "${PACKAGE_ROOT}/.venv/bin/python" -m "${APP_MODULE}" >> "${RUN_LOG_FILE}" 2>&1 &
    echo "$!" > "${PID_FILE}"
  )

  local new_pid
  new_pid="$(cat "${PID_FILE}")"
  log "Service started, pid=${new_pid}"
  log "Log file: ${RUN_LOG_FILE}"
}

wait_for_health() {
  local url="http://127.0.0.1:${SERVICE_PORT}/health"
  local elapsed=0
  local code
  local body

  while (( elapsed < HEALTH_TIMEOUT_SECONDS )); do
    code="$(curl -sS -o /tmp/rag_stream_health_body.txt -w '%{http_code}' "${url}" || true)"
    body="$(cat /tmp/rag_stream_health_body.txt 2>/dev/null || true)"

    if [[ "${code}" == "200" ]] && [[ "${body}" == *'"status":"ok"'* ]]; then
      log "Health check passed: ${body}"
      return 0
    fi

    sleep 1
    elapsed=$((elapsed + 1))
  done

  fail "Health check failed after ${HEALTH_TIMEOUT_SECONDS}s. Check logs: ${RUN_LOG_FILE}"
}

main() {
  require_command uv
  require_command curl
  require_command nohup

  load_env_file_if_exists
  ensure_venv_and_dependencies
  ensure_not_running
  start_service
  wait_for_health
  log "Service is ready at http://127.0.0.1:${SERVICE_PORT}"
}

main "$@"
