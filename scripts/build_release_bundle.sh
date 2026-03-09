#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PACKAGE_DATE="${PACKAGE_DATE:-$(date +%F)}"
BUNDLE_NAME="${BUNDLE_NAME:-daishan_release_${PACKAGE_DATE}}"
DIST_DIR="${DIST_DIR:-${SCRIPT_DIR}/dist}"
STAGING_DIR="${DIST_DIR}/${BUNDLE_NAME}"
ARCHIVE_PATH="${DIST_DIR}/${BUNDLE_NAME}.tar.gz"
MANIFEST_FILE="${MANIFEST_FILE:-${SCRIPT_DIR}/release_bundle_manifest.txt}"

EXCLUDE_PATTERNS=(
  "__pycache__/"
  "*.pyc"
  "*.pyo"
  ".pytest_cache/"
  ".log-manager/"
  ".venv/"
  "logs/"
  "tmp*/"
  ".DS_Store"
  ".env"
)

log() {
  printf '[bundle] %s\n' "$*"
}

fail() {
  printf '[bundle][error] %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"
}

copy_entry() {
  local relative_path="$1"
  local source_path="${PROJECT_ROOT}/${relative_path}"
  local target_path="${STAGING_DIR}/${relative_path}"

  [[ -e "${source_path}" ]] || fail "Manifest path not found: ${relative_path}"

  if [[ "${relative_path}" == "src" ]]; then
    local rsync_excludes=()
    local pattern
    for pattern in "${EXCLUDE_PATTERNS[@]}"; do
      rsync_excludes+=(--exclude "${pattern}")
    done
    mkdir -p "${target_path}"
    rsync -a "${rsync_excludes[@]}" "${source_path}/" "${target_path}/"
    return
  fi

  mkdir -p "$(dirname "${target_path}")"
  cp -a "${source_path}" "${target_path}"
}

main() {
  require_command tar
  require_command rsync

  [[ -f "${MANIFEST_FILE}" ]] || fail "Manifest not found: ${MANIFEST_FILE}"

  rm -rf "${STAGING_DIR}"
  mkdir -p "${DIST_DIR}" "${STAGING_DIR}"
  : > "${STAGING_DIR}/PACKAGED_ITEMS.txt"

  while IFS= read -r line || [[ -n "${line}" ]]; do
    local trimmed="${line#"${line%%[![:space:]]*}"}"
    trimmed="${trimmed%"${trimmed##*[![:space:]]}"}"
    [[ -z "${trimmed}" ]] && continue
    [[ "${trimmed}" =~ ^# ]] && continue

    copy_entry "${trimmed}"
    printf '%s\n' "${trimmed}" >> "${STAGING_DIR}/PACKAGED_ITEMS.txt"
    log "Included: ${trimmed}"
  done < "${MANIFEST_FILE}"

  rm -f "${ARCHIVE_PATH}"
  tar -C "${DIST_DIR}" -czf "${ARCHIVE_PATH}" "${BUNDLE_NAME}"

  log "Bundle directory: ${STAGING_DIR}"
  log "Archive created: ${ARCHIVE_PATH}"
}

main "$@"
