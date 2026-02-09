#!/usr/bin/env bash
set -euo pipefail

AGENTS_FILE="${1:-AGENTS.md}"
RULES_DIR="${RULES_DIR:-.codex/company-rules}"

BEGIN_MARKER="<!-- BEGIN AUTO-RULES -->"
END_MARKER="<!-- END AUTO-RULES -->"

if [[ ! -f "$AGENTS_FILE" ]]; then
  echo "[ERROR] AGENTS file not found: $AGENTS_FILE" >&2
  exit 1
fi

if [[ ! -d "$RULES_DIR" ]]; then
  echo "[ERROR] Rules directory not found: $RULES_DIR" >&2
  echo "        You can override with: RULES_DIR=<path> $0 $AGENTS_FILE" >&2
  exit 1
fi

tmp_block="$(mktemp)"
tmp_out="$(mktemp)"
cleanup() {
  rm -f "$tmp_block" "$tmp_out"
}
trap cleanup EXIT

rule_files=()
while IFS= read -r file; do
  rule_files+=("$file")
done < <(find "$RULES_DIR" -maxdepth 1 -type f \( -name '*.md' -o -name '*.markdown' \) | sort)

{
  echo "$BEGIN_MARKER"
  echo ""
  echo "## Rules Snapshot"
  echo ""
  echo "以下内容由 \`.codex/skills/project-init/scripts/inject-company-rules.sh\` 自动注入。"
  echo "源目录：\`$RULES_DIR\`"
  echo ""

  if [[ ${#rule_files[@]} -eq 0 ]]; then
    echo "_No markdown files found in \`$RULES_DIR\`._"
  else
    for file in "${rule_files[@]}"; do
      echo "---"
      echo ""
      echo "## Source: $file"
      echo ""
      cat "$file"
      echo ""
    done
  fi

  echo "$END_MARKER"
} > "$tmp_block"

has_begin=0
has_end=0
grep -Fq "$BEGIN_MARKER" "$AGENTS_FILE" && has_begin=1
grep -Fq "$END_MARKER" "$AGENTS_FILE" && has_end=1
legacy_source_regex='^## Source: .*/[^/]+\.(md|markdown)$'

if [[ $has_begin -eq 1 && $has_end -eq 1 ]]; then
  awk -v begin="$BEGIN_MARKER" -v end="$END_MARKER" -v block_file="$tmp_block" '
    BEGIN {
      while ((getline line < block_file) > 0) {
        block = block line ORS
      }
      close(block_file)
    }
    {
      if ($0 == begin) {
        printf "%s", block
        skipping = 1
        next
      }
      if (skipping && $0 == end) {
        skipping = 0
        next
      }
      if (!skipping) {
        print
      }
    }
  ' "$AGENTS_FILE" > "$tmp_out"
elif [[ $has_begin -eq 0 && $has_end -eq 0 ]]; then
  if grep -Eq "$legacy_source_regex" "$AGENTS_FILE"; then
    first_legacy_line="$(grep -nE "$legacy_source_regex" "$AGENTS_FILE" | head -n1 | cut -d: -f1)"
    if [[ -n "$first_legacy_line" && "$first_legacy_line" -gt 1 ]]; then
      head -n "$((first_legacy_line - 1))" "$AGENTS_FILE" > "$tmp_out"
      while [[ -s "$tmp_out" ]]; do
        last_line="$(tail -n 1 "$tmp_out")"
        if [[ -z "$last_line" || "$last_line" == "---" ]]; then
          sed -i '' '$d' "$tmp_out"
        else
          break
        fi
      done
    else
      : > "$tmp_out"
    fi
  else
    cat "$AGENTS_FILE" > "$tmp_out"
  fi

  if [[ -s "$tmp_out" && "$(tail -c 1 "$tmp_out" || true)" != "" ]]; then
    echo >> "$tmp_out"
  fi
  echo >> "$tmp_out"
  cat "$tmp_block" >> "$tmp_out"
else
  echo "[ERROR] Marker mismatch in $AGENTS_FILE" >&2
  echo "        Ensure both markers exist or both are absent:" >&2
  echo "        $BEGIN_MARKER" >&2
  echo "        $END_MARKER" >&2
  exit 1
fi

mv "$tmp_out" "$AGENTS_FILE"
echo "[OK] Updated $AGENTS_FILE from $RULES_DIR"
