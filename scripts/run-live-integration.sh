#!/usr/bin/env bash
set -u -o pipefail

ENV_FILE=".env.testnet"
EVIDENCE_DIR="docs/evidence"
MAX_LOG_LINES=120
SKIP_SMOKE_NETWORK=0

usage() {
  cat <<'EOF'
Usage:
  ./scripts/run-live-integration.sh [--env-file FILE] [--evidence-dir DIR] [--max-log-lines N] [--skip-smoke-network]

Runs the live integration sequence:
1) scripts/validate-testnet-env.py
2) scripts/run-testnet-smoke.sh
3) HEDERA_SHIELD_RUN_INTEGRATION=1 pytest -q tests/test_integration_testnet.py

Writes timestamped evidence markdown to docs/evidence by default.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      ENV_FILE="${2:-}"
      shift 2
      ;;
    --evidence-dir)
      EVIDENCE_DIR="${2:-}"
      shift 2
      ;;
    --max-log-lines)
      MAX_LOG_LINES="${2:-}"
      shift 2
      ;;
    --skip-smoke-network)
      SKIP_SMOKE_NETWORK=1
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

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TIMESTAMP_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$EVIDENCE_DIR"
EVIDENCE_FILE="$EVIDENCE_DIR/live-integration-${TIMESTAMP_UTC}.md"

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

VALIDATOR_LOG="$TMP_DIR/validator.log"
SMOKE_LOG="$TMP_DIR/smoke.log"
INTEGRATION_LOG="$TMP_DIR/integration.log"

VALIDATOR_EXIT=1
SMOKE_EXIT=1
INTEGRATION_EXIT=1

python3 scripts/validate-testnet-env.py "$ENV_FILE" >"$VALIDATOR_LOG" 2>&1
VALIDATOR_EXIT=$?

if [[ $SKIP_SMOKE_NETWORK -eq 1 ]]; then
  HEDERA_SHIELD_SMOKE_SKIP_NETWORK=1 ./scripts/run-testnet-smoke.sh "$ENV_FILE" >"$SMOKE_LOG" 2>&1
else
  ./scripts/run-testnet-smoke.sh "$ENV_FILE" >"$SMOKE_LOG" 2>&1
fi
SMOKE_EXIT=$?

HEDERA_SHIELD_RUN_INTEGRATION=1 pytest -q tests/test_integration_testnet.py >"$INTEGRATION_LOG" 2>&1
INTEGRATION_EXIT=$?

status_text() {
  if [[ "$1" -eq 0 ]]; then
    printf 'PASS'
  else
    printf 'FAIL'
  fi
}

VALIDATOR_STATUS="$(status_text "$VALIDATOR_EXIT")"
SMOKE_STATUS="$(status_text "$SMOKE_EXIT")"
INTEGRATION_STATUS="$(status_text "$INTEGRATION_EXIT")"

OVERALL_EXIT=0
if [[ $VALIDATOR_EXIT -ne 0 || $SMOKE_EXIT -ne 0 || $INTEGRATION_EXIT -ne 0 ]]; then
  OVERALL_EXIT=1
fi
OVERALL_STATUS="$(status_text "$OVERALL_EXIT")"

PYTEST_SUMMARY_LINE="$(tail -n 20 "$INTEGRATION_LOG" | grep -E '[0-9]+ passed|[0-9]+ failed|[0-9]+ skipped' | tail -n 1 || true)"
if [[ -z "$PYTEST_SUMMARY_LINE" ]]; then
  PYTEST_SUMMARY_LINE="summary not found"
fi

{
  echo "# Live Integration Evidence"
  echo
  echo "- Timestamp (UTC): \`$TIMESTAMP_UTC\`"
  echo "- Env file: \`$ENV_FILE\`"
  echo "- Overall: \`$OVERALL_STATUS\`"
  echo
  echo "## Command Status"
  echo "- \`python3 scripts/validate-testnet-env.py $ENV_FILE\`: \`$VALIDATOR_STATUS\` (exit $VALIDATOR_EXIT)"
  echo "- \`./scripts/run-testnet-smoke.sh $ENV_FILE\`: \`$SMOKE_STATUS\` (exit $SMOKE_EXIT)"
  echo "- \`HEDERA_SHIELD_RUN_INTEGRATION=1 pytest -q tests/test_integration_testnet.py\`: \`$INTEGRATION_STATUS\` (exit $INTEGRATION_EXIT)"
  echo "- Integration pytest summary: \`$PYTEST_SUMMARY_LINE\`"
  echo
  echo "## Validator Output"
  echo '```text'
  sed -n "1,${MAX_LOG_LINES}p" "$VALIDATOR_LOG"
  echo '```'
  echo
  echo "## Smoke Output"
  echo '```text'
  sed -n "1,${MAX_LOG_LINES}p" "$SMOKE_LOG"
  echo '```'
  echo
  echo "## Integration Pytest Output"
  echo '```text'
  sed -n "1,${MAX_LOG_LINES}p" "$INTEGRATION_LOG"
  echo '```'
} >"$EVIDENCE_FILE"

printf 'LIVE|evidence|%s|%s\n' "$OVERALL_STATUS" "$EVIDENCE_FILE"
exit "$OVERALL_EXIT"
