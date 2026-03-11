#!/usr/bin/env bash
set -u -o pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${1:-.env.testnet.example}"
ARTIFACTS_DIR="artifacts/demo/smoke-local"
HARNESS_LOG="$ARTIFACTS_DIR/harness.stdout.log"

PASS_COUNT=0
FAIL_COUNT=0

emit() {
  local check="$1"
  local status="$2"
  local details="$3"
  printf 'SMOKE|%s|%s|%s\n' "$check" "$status" "$details"
}

pass() {
  local check="$1"
  local details="$2"
  PASS_COUNT=$((PASS_COUNT + 1))
  emit "$check" "PASS" "$details"
}

fail() {
  local check="$1"
  local details="$2"
  FAIL_COUNT=$((FAIL_COUNT + 1))
  emit "$check" "FAIL" "$details"
}

if command -v python3 >/dev/null 2>&1; then
  pass "python3" "python3 available"
else
  fail "python3" "python3 is required"
fi

if command -v ruff >/dev/null 2>&1; then
  pass "ruff" "ruff available"
else
  fail "ruff" "ruff not found (install in active environment)"
fi

if command -v pytest >/dev/null 2>&1; then
  pass "pytest" "pytest available"
else
  fail "pytest" "pytest not found (install in active environment)"
fi

if [[ -f "$ENV_FILE" ]]; then
  pass "env_file" "found $ENV_FILE"
else
  fail "env_file" "missing $ENV_FILE"
fi

if [[ -f "$ENV_FILE" ]]; then
  if python3 scripts/validate-testnet-env.py "$ENV_FILE" >/dev/null 2>&1; then
    pass "env_validation" "env format accepted"
  else
    fail "env_validation" "env format validation failed for $ENV_FILE"
  fi
fi

mkdir -p "$ARTIFACTS_DIR"
if ./scripts/run-integration-harness.sh --mode mock --env-file "$ENV_FILE" --artifacts-dir "$ARTIFACTS_DIR/harness" >"$HARNESS_LOG" 2>&1; then
  pass "harness_mock" "mock harness passed; artifacts at $ARTIFACTS_DIR/harness"
else
  fail "harness_mock" "mock harness failed; inspect $HARNESS_LOG"
fi

if [[ -f "$ARTIFACTS_DIR/harness/report.md" && -f "$ARTIFACTS_DIR/harness/report.json" ]]; then
  pass "artifacts" "report.md and report.json generated"
else
  fail "artifacts" "expected harness reports not found"
fi

TOTAL=$((PASS_COUNT + FAIL_COUNT))
if [[ $FAIL_COUNT -eq 0 ]]; then
  emit "summary" "PASS" "${PASS_COUNT}/${TOTAL} checks passed"
  exit 0
fi

emit "summary" "FAIL" "${FAIL_COUNT}/${TOTAL} checks failed"
exit 1
