#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
OUTPUT_ZIP="$DIST_DIR/submission-bundle.zip"

emit() {
  local check="$1"
  local status="$2"
  local details="$3"
  printf 'PACKAGE|%s|%s|%s\n' "$check" "$status" "$details"
}

required_files=(
  "README.md"
  "SUBMISSION.md"
  "DEPLOY_STATUS.md"
  "docs/TESTNET_SETUP.md"
  "docs/TESTNET_EVIDENCE.md"
  "docs/DEPLOY_PROOF.md"
  "docs/DEMO_RECORDING_RUNBOOK.md"
  "docs/FINAL_SUBMISSION_CHECKLIST.md"
  ".env.testnet.example"
  "scripts/run-integration-harness.sh"
  "scripts/run-testnet-smoke.sh"
  "scripts/capture-testnet-evidence.sh"
  "scripts/generate-integration-evidence.py"
  "scripts/package-submission.sh"
  "scripts/release-evidence.sh"
  "scripts/generate-handoff-index.py"
  "scripts/submission-readiness.sh"
  "scripts/sync-and-submit.sh"
  "scripts/offline-handoff.sh"
)

missing=()
for rel_path in "${required_files[@]}"; do
  if [[ ! -f "$ROOT_DIR/$rel_path" ]]; then
    missing+=("$rel_path")
  fi
done

if (( ${#missing[@]} > 0 )); then
  emit "required_files" "FAIL" "missing required files: ${missing[*]}"
  exit 1
fi

emit "required_files" "PASS" "all required files present"

optional_files=()
if [[ -d "$ROOT_DIR/artifacts/integration" ]]; then
  while IFS= read -r file_path; do
    rel_path="${file_path#"$ROOT_DIR/"}"
    optional_files+=("$rel_path")
  done < <(
    find "$ROOT_DIR/artifacts/integration" -type f \
      \( -name 'report.md' -o -name 'report.json' -o -name 'harness.log' -o -name 'validator.log' -o -name 'smoke.log' -o -name 'integration.log' \) \
      | sort
  )
fi

mkdir -p "$DIST_DIR"

tmp_list="$(mktemp)"
cleanup() {
  rm -f "$tmp_list"
}
trap cleanup EXIT

for rel_path in "${required_files[@]}"; do
  printf '%s\n' "$rel_path" >> "$tmp_list"
done

for rel_path in "${optional_files[@]}"; do
  printf '%s\n' "$rel_path" >> "$tmp_list"
done

python3 - "$ROOT_DIR" "$OUTPUT_ZIP" "$tmp_list" <<'PY'
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

root = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
listing = Path(sys.argv[3]).resolve()

entries = [line.strip() for line in listing.read_text(encoding="utf-8").splitlines() if line.strip()]

with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for rel in entries:
        path = (root / rel).resolve()
        if not path.exists() or not path.is_file():
            raise SystemExit(f"missing path during archive creation: {rel}")
        zf.write(path, arcname=rel)
PY

file_count="$(python3 - "$OUTPUT_ZIP" <<'PY'
from __future__ import annotations

import sys
import zipfile

archive = sys.argv[1]
with zipfile.ZipFile(archive, "r") as zf:
    print(len(zf.infolist()))
PY
)"

emit "bundle" "PASS" "created $OUTPUT_ZIP with $file_count files"
