#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

fail_count=0

emit() {
  local check="$1"
  local status="$2"
  local details="$3"
  printf 'HANDOFF|%s|%s|%s\n' "$check" "$status" "$details"
}

check_file() {
  local rel_path="$1"
  if [[ -f "$ROOT_DIR/$rel_path" ]]; then
    emit "file" "PASS" "found $rel_path"
  else
    emit "file" "FAIL" "missing $rel_path"
    fail_count=$((fail_count + 1))
  fi
}

check_contains() {
  local rel_path="$1"
  local pattern="$2"
  local label="$3"
  if [[ ! -f "$ROOT_DIR/$rel_path" ]]; then
    emit "$label" "FAIL" "missing $rel_path"
    fail_count=$((fail_count + 1))
    return
  fi

  if grep -Fq -- "$pattern" "$ROOT_DIR/$rel_path"; then
    emit "$label" "PASS" "found '$pattern' in $rel_path"
  else
    emit "$label" "FAIL" "missing '$pattern' in $rel_path"
    fail_count=$((fail_count + 1))
  fi
}

check_file "README.md"
check_file "SUBMISSION.md"
check_file "RELEASE_READINESS.md"
check_file "SUBMISSION_DRY_RUN.md"
check_file "HEDERA_PORTAL_SUBMISSION_PACKET.md"
check_file "docs/FINAL_SUBMISSION_CHECKLIST.md"
check_file "dist/submission-readiness-latest.txt"
check_file "dist/pre-submit-verify-latest.txt"
check_file "dist/portal-submission/portal-submission-verify-latest.txt"
check_file "dist/submission-freeze/submission-freeze-latest.md"
check_file "dist/submission-freeze/submission-freeze-latest.json"

check_contains "dist/submission-readiness-latest.txt" "- Overall: PASS" "readiness_summary"
check_contains "dist/submission-readiness-latest.txt" "READINESS|" "readiness_checks"
check_contains "dist/pre-submit-verify-latest.txt" "- Overall: PASS" "verify_summary"
check_contains "dist/pre-submit-verify-latest.txt" "VERIFY|" "verify_checks"
check_contains "dist/portal-submission/portal-submission-verify-latest.txt" "- Overall: PASS" "portal_verify_summary"
check_contains "dist/portal-submission/portal-submission-verify-latest.txt" "PORTAL_VERIFY|" "portal_verify_checks"

if (( fail_count > 0 )); then
  emit "summary" "FAIL" "$fail_count required checks failed"
  exit 1
fi

emit "summary" "PASS" "all required files/checks present"

current_branch="$(git rev-parse --abbrev-ref HEAD)"
current_sha="$(git rev-parse HEAD)"

cat <<EOF

Final operator actions before portal submit:
1. Confirm clean tree: git status --short
2. Confirm branch/SHA:
   - branch: $current_branch
   - sha:    $current_sha
3. Re-run gates:
   - ./scripts/pre_submit_guard.sh
   - ./scripts/submission-readiness.sh
   - ./scripts/pre-submit-verify.py
4. Refresh packet/freeze:
   - ./scripts/generate-portal-submission-packet.py
   - ./scripts/verify-portal-submission-packet.py
   - ./scripts/submission-freeze.py
   - ./scripts/verify-submission-freeze.py
5. Open HEDERA_PORTAL_SUBMISSION_PACKET.md and paste into portal fields.
6. Validate all links are public and SHA in portal equals: $current_sha
7. Submit and capture confirmation screenshot + UTC timestamp.

EOF
