#!/usr/bin/env bash
set -u -o pipefail

MODE="mock"
ENV_FILE=".env.testnet"
ARTIFACTS_DIR="artifacts/integration/$(date -u +%Y%m%dT%H%M%SZ)"
SKIP_INTEGRATION_TESTS=0

usage() {
  cat <<'EOF'
Usage:
  ./scripts/run-integration-harness.sh [--mode mock|real] [--env-file FILE] [--artifacts-dir DIR] [--skip-integration-tests]

Modes:
  mock  Default. Offline-safe run: env validation + smoke checks with network probe disabled.
  real  Read-only live run: env validation + live smoke probe + optional live pytest integration suite.

Safety:
  - Defaults to mock mode to avoid accidental network/state actions.
  - real mode requires explicit opt-in: HEDERA_SHIELD_ENABLE_REAL_TESTNET=1
  - This harness does not execute HTS enforcement actions.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="${2:-}"
      shift 2
      ;;
    --env-file)
      ENV_FILE="${2:-}"
      shift 2
      ;;
    --artifacts-dir)
      ARTIFACTS_DIR="${2:-}"
      shift 2
      ;;
    --skip-integration-tests)
      SKIP_INTEGRATION_TESTS=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ "$MODE" != "mock" && "$MODE" != "real" ]]; then
  echo "Invalid --mode value: $MODE (expected mock|real)" >&2
  exit 2
fi

mkdir -p "$ARTIFACTS_DIR"
HARNESS_LOG="$ARTIFACTS_DIR/harness.log"
VALIDATOR_LOG="$ARTIFACTS_DIR/validator.log"
SMOKE_LOG="$ARTIFACTS_DIR/smoke.log"
INTEGRATION_LOG="$ARTIFACTS_DIR/integration.log"

HARNESS_EXIT=0
VALIDATOR_EXIT=1
SMOKE_EXIT=1
INTEGRATION_EXIT="SKIP"
REAL_ALLOWED=0

emit() {
  local check="$1"
  local status="$2"
  local details="$3"
  local line
  line="HARNESS|$check|$status|$details"
  printf '%s\n' "$line"
  printf '%s\n' "$line" >> "$HARNESS_LOG"
}

fail() {
  local check="$1"
  local details="$2"
  HARNESS_EXIT=1
  emit "$check" "FAIL" "$details"
}

pass() {
  local check="$1"
  local details="$2"
  emit "$check" "PASS" "$details"
}

skip() {
  local check="$1"
  local details="$2"
  emit "$check" "SKIP" "$details"
}

read_env_value() {
  local key="$1"
  local file="$2"
  awk -v wanted="$key" '
    BEGIN { FS = "=" }
    /^[[:space:]]*#/ { next }
    /^[[:space:]]*$/ { next }
    $0 !~ /=/ { next }
    {
      k = $1
      sub(/^[[:space:]]+/, "", k)
      sub(/[[:space:]]+$/, "", k)
      if (k == wanted) {
        value = substr($0, index($0, "=") + 1)
        sub(/[[:space:]]+#.*/, "", value)
        sub(/^[[:space:]]+/, "", value)
        sub(/[[:space:]]+$/, "", value)
        print value
        exit 0
      }
    }
  ' "$file"
}

is_placeholder_account() {
  local value="$1"
  [[ "$value" =~ ^0\.0\.(YOUR_[A-Z0-9_]+|PLACEHOLDER|EXAMPLE)$ ]]
}

is_placeholder_key() {
  local value="$1"
  [[ "$value" =~ ^(YOUR_[A-Z0-9_]+|your_[a-z0-9_]+|<[^>]+>)$ ]]
}

printf '' > "$HARNESS_LOG"
pass "mode" "running mode=$MODE"
pass "artifacts" "writing artifacts to $ARTIFACTS_DIR"

if [[ ! -f "$ENV_FILE" ]]; then
  fail "env_file" "missing file: $ENV_FILE"
  VALIDATOR_EXIT=1
  SMOKE_EXIT=1
  INTEGRATION_EXIT="SKIP"
else
  pass "env_file" "found $ENV_FILE"

  python3 scripts/validate-testnet-env.py "$ENV_FILE" > "$VALIDATOR_LOG" 2>&1
  VALIDATOR_EXIT=$?
  if [[ $VALIDATOR_EXIT -eq 0 ]]; then
    pass "validator" "env file format accepted"
  else
    fail "validator" "env validation failed; see $VALIDATOR_LOG"
  fi

  if [[ "$MODE" == "real" ]]; then
    NETWORK="$(read_env_value "HEDERA_SHIELD_HEDERA_NETWORK" "$ENV_FILE")"
    OPERATOR_ID="$(read_env_value "HEDERA_SHIELD_HEDERA_OPERATOR_ID" "$ENV_FILE")"
    OPERATOR_KEY="$(read_env_value "HEDERA_SHIELD_HEDERA_OPERATOR_KEY" "$ENV_FILE")"

    if [[ "${HEDERA_SHIELD_ENABLE_REAL_TESTNET:-0}" != "1" ]]; then
      fail "real_opt_in" "set HEDERA_SHIELD_ENABLE_REAL_TESTNET=1 to run real mode"
    else
      pass "real_opt_in" "explicit real mode opt-in enabled"
    fi

    if [[ "$NETWORK" != "testnet" ]]; then
      fail "real_network" "real mode currently requires HEDERA_SHIELD_HEDERA_NETWORK=testnet"
    else
      pass "real_network" "network is testnet"
    fi

    if [[ -z "$OPERATOR_ID" || -z "$OPERATOR_KEY" ]]; then
      fail "real_creds" "operator id/key must be present for real mode"
    elif is_placeholder_account "$OPERATOR_ID" || is_placeholder_key "$OPERATOR_KEY"; then
      fail "real_creds" "replace placeholder operator id/key before real mode"
    else
      pass "real_creds" "operator credentials look non-placeholder"
    fi

    if [[ $HARNESS_EXIT -eq 0 ]]; then
      REAL_ALLOWED=1
    fi
  fi

  if [[ "$MODE" == "mock" || $REAL_ALLOWED -eq 0 ]]; then
    HEDERA_SHIELD_SMOKE_SKIP_NETWORK=1 ./scripts/run-testnet-smoke.sh "$ENV_FILE" > "$SMOKE_LOG" 2>&1
  else
    ./scripts/run-testnet-smoke.sh "$ENV_FILE" > "$SMOKE_LOG" 2>&1
  fi
  SMOKE_EXIT=$?
  if [[ $SMOKE_EXIT -eq 0 ]]; then
    pass "smoke" "smoke checks passed"
  else
    fail "smoke" "smoke checks failed; see $SMOKE_LOG"
  fi

  if [[ "$MODE" == "real" ]]; then
    if [[ $SKIP_INTEGRATION_TESTS -eq 1 ]]; then
      INTEGRATION_EXIT="SKIP"
      skip "integration_pytest" "skipped via --skip-integration-tests"
      : > "$INTEGRATION_LOG"
    elif [[ $HARNESS_EXIT -ne 0 ]]; then
      INTEGRATION_EXIT="SKIP"
      skip "integration_pytest" "skipped due to prior failures"
      : > "$INTEGRATION_LOG"
    else
      HEDERA_SHIELD_RUN_INTEGRATION=1 pytest -q tests/test_integration_testnet.py > "$INTEGRATION_LOG" 2>&1
      INTEGRATION_EXIT=$?
      if [[ $INTEGRATION_EXIT -eq 0 ]]; then
        pass "integration_pytest" "live integration tests passed"
      else
        fail "integration_pytest" "live integration tests failed; see $INTEGRATION_LOG"
      fi
    fi
  else
    INTEGRATION_EXIT="SKIP"
    skip "integration_pytest" "mock mode skips live integration pytest"
    : > "$INTEGRATION_LOG"
  fi
fi

GEN_ARGS=(
  --mode "$MODE"
  --env-file "$ENV_FILE"
  --artifacts-dir "$ARTIFACTS_DIR"
  --validator-exit "$VALIDATOR_EXIT"
  --smoke-exit "$SMOKE_EXIT"
  --harness-exit "$HARNESS_EXIT"
)
if [[ "$INTEGRATION_EXIT" != "SKIP" ]]; then
  GEN_ARGS+=(--integration-exit "$INTEGRATION_EXIT")
fi

if python3 scripts/generate-integration-evidence.py "${GEN_ARGS[@]}" > /dev/null 2>&1; then
  pass "report" "generated $ARTIFACTS_DIR/report.md and report.json"
else
  fail "report" "failed to generate evidence report"
fi

if [[ $HARNESS_EXIT -eq 0 ]]; then
  emit "summary" "PASS" "harness checks passed"
  exit 0
fi

emit "summary" "FAIL" "one or more harness checks failed"
exit 1
