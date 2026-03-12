#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DEMO_ID="${1:-3min-offline}"
DEMO_DIR="$ROOT_DIR/artifacts/demo/$DEMO_ID"

fail() {
  local message="$1"
  printf 'GUARD|FAIL|%s\n' "$message" >&2
  exit 1
}

pass() {
  local message="$1"
  printf 'GUARD|PASS|%s\n' "$message"
}

check_file() {
  local rel_path="$1"
  local path="$ROOT_DIR/$rel_path"
  [[ -f "$path" ]] || fail "missing file: $rel_path"
  pass "found file: $rel_path"
}

check_glob() {
  local pattern="$1"
  compgen -G "$ROOT_DIR/$pattern" > /dev/null || fail "missing artifact pattern: $pattern"
  pass "found artifact pattern: $pattern"
}

check_file "README.md"
check_file "SUBMISSION.md"
check_file "SUBMISSION_PACKET.md"
check_file "HEDERA_PORTAL_SUBMISSION_PACKET.md"
check_file "RELEASE_READINESS.md"
check_file "docs/FINAL_SUBMISSION_CHECKLIST.md"
check_file "dist/submission-readiness-latest.txt"
check_file "dist/pre-submit-verify-latest.txt"
check_file "dist/submission-bundle.zip"
check_file "dist/portal-submission/portal-submission-packet-latest.md"
check_file "dist/portal-submission/portal-submission-verify-latest.txt"
check_file "dist/submission-freeze/submission-freeze-latest.md"
check_file "dist/submission-freeze/submission-freeze-latest.json"
check_file "artifacts/demo/$DEMO_ID/harness/report.md"
check_file "artifacts/demo/$DEMO_ID/harness/report.json"
check_file "artifacts/demo/$DEMO_ID/harness/harness.log"
check_file "artifacts/demo/$DEMO_ID/harness/smoke.log"
check_file "artifacts/demo/$DEMO_ID/harness/validator.log"
check_file "artifacts/demo/$DEMO_ID/submission-bundle.zip.sha256"
check_glob "dist/release-evidence-*.tar.gz"
check_glob "artifacts/integration/release-*/release-report.md"
check_glob "artifacts/integration/release-*/release-report.json"

pass "pre-submit guard complete (demo-id=$DEMO_ID)"
