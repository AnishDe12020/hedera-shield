#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

check_path() {
  local rel_path="$1"
  if [[ -e "$ROOT_DIR/$rel_path" ]]; then
    printf 'CHECK|PASS|%s\n' "$rel_path"
  else
    printf 'CHECK|MISSING|%s\n' "$rel_path"
  fi
}

echo "HederaShield Submit-Now Operator Checklist"
echo "UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo
echo "Final steps"
echo "1) Run pre-submit checks:"
echo "   - ./scripts/pre_submit_guard.sh"
echo "   - ./scripts/submission-readiness.sh"
echo "   - ./scripts/pre-submit-verify.py"
echo "2) Print/verify packet paths shown below."
echo "3) Fill portal fields from docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json"
echo "   (fallback: HEDERA_PORTAL_SUBMISSION_PACKET.md)."
echo "4) Replace all placeholders with final public links + commit SHA."
echo "5) Submit in portal and capture confirmation screenshot + UTC timestamp."
echo
echo "Key artifact paths"
check_path "docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json"
check_path "HEDERA_PORTAL_SUBMISSION_PACKET.md"
check_path "SUBMISSION_PACKET.md"
check_path "RELEASE_READINESS.md"
check_path "SUBMISSION.md"
check_path "dist/submission-readiness-latest.txt"
check_path "dist/pre-submit-verify-latest.txt"
check_path "dist/portal-submission/portal-submission-packet-latest.md"
check_path "dist/portal-submission/portal-submission-verify-latest.txt"
check_path "dist/submission-freeze/submission-freeze-latest.md"
check_path "dist/submission-freeze/submission-freeze-latest.json"

echo
echo "Reference commands"
echo "- ./scripts/generate-portal-submission-packet.py"
echo "- ./scripts/verify-portal-submission-packet.py"
echo "- ./scripts/submission-freeze.py"
echo "- ./scripts/verify-submission-freeze.py"
