#!/usr/bin/env bash
set -u -o pipefail

ENV_FILE=".env.testnet.example"
ARTIFACTS_ROOT="artifacts/integration"
DIST_DIR="dist"
INCLUDE_REAL_TESTNET=0

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/release-evidence.sh [--env-file FILE] [--artifacts-root DIR] [--dist-dir DIR] [--include-real-testnet]

Default behavior (safe):
  - Runs lint and tests
  - Runs mock integration harness (no live network probe)
  - Builds dist/submission-bundle.zip
  - Creates dist/release-evidence-<timestamp>.tar.gz

Optional real testnet behavior:
  --include-real-testnet requires HEDERA_SHIELD_ENABLE_REAL_TESTNET=1.
  When enabled, the script also runs the real-mode integration harness and captures
  testnet evidence into the release artifact directory.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      ENV_FILE="${2:-}"
      shift 2
      ;;
    --artifacts-root)
      ARTIFACTS_ROOT="${2:-}"
      shift 2
      ;;
    --dist-dir)
      DIST_DIR="${2:-}"
      shift 2
      ;;
    --include-real-testnet)
      INCLUDE_REAL_TESTNET=1
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
RELEASE_DIR="$ARTIFACTS_ROOT/release-$TIMESTAMP_UTC"
MOCK_ARTIFACTS_DIR="$RELEASE_DIR/mock"
REAL_ARTIFACTS_DIR="$RELEASE_DIR/real"
LOG_DIR="$RELEASE_DIR/logs"
mkdir -p "$MOCK_ARTIFACTS_DIR" "$LOG_DIR" "$DIST_DIR"

LINT_LOG="$LOG_DIR/lint.log"
PYTEST_LOG="$LOG_DIR/pytest.log"
MOCK_HARNESS_LOG="$LOG_DIR/mock-harness.log"
REAL_HARNESS_LOG="$LOG_DIR/real-harness.log"
REAL_EVIDENCE_LOG="$LOG_DIR/real-evidence.log"
PACKAGE_LOG="$LOG_DIR/package-submission.log"
SUMMARY_LOG="$RELEASE_DIR/release-summary.log"
REPORT_MD="$RELEASE_DIR/release-report.md"
REPORT_JSON="$RELEASE_DIR/release-report.json"

RELEASE_TAR_GZ="$DIST_DIR/release-evidence-$TIMESTAMP_UTC.tar.gz"
SUBMISSION_ZIP="$DIST_DIR/submission-bundle.zip"

LINT_EXIT=1
PYTEST_EXIT=1
MOCK_EXIT=1
REAL_EXIT="SKIP"
REAL_EVIDENCE_EXIT="SKIP"
PACKAGE_EXIT=1
TAR_EXIT=1
OVERALL_EXIT=0

emit() {
  local check="$1"
  local status="$2"
  local details="$3"
  local line
  line="RELEASE|$check|$status|$details"
  printf '%s\n' "$line"
  printf '%s\n' "$line" >> "$SUMMARY_LOG"
}

status_for_exit() {
  local code="$1"
  if [[ "$code" == "0" ]]; then
    printf 'PASS'
  elif [[ "$code" == "SKIP" ]]; then
    printf 'SKIP'
  else
    printf 'FAIL'
  fi
}

run_with_log() {
  local check="$1"
  local log_file="$2"
  shift 2

  "$@" > "$log_file" 2>&1
  local exit_code=$?
  if [[ $exit_code -eq 0 ]]; then
    emit "$check" "PASS" "command succeeded; see $log_file"
  else
    emit "$check" "FAIL" "command failed (exit $exit_code); see $log_file"
  fi
  return "$exit_code"
}

: > "$SUMMARY_LOG"
emit "release_dir" "PASS" "writing artifacts to $RELEASE_DIR"
emit "default_mode" "PASS" "using mock harness by default"

LINT_CMD=(ruff check hedera_shield/ tests/)
if ! command -v ruff >/dev/null 2>&1; then
  LINT_CMD=(python3 -m ruff check hedera_shield/ tests/)
fi

if run_with_log "lint" "$LINT_LOG" "${LINT_CMD[@]}"; then
  LINT_EXIT=0
else
  LINT_EXIT=$?
  OVERALL_EXIT=1
fi

if run_with_log "pytest" "$PYTEST_LOG" pytest tests/ -v --tb=short; then
  PYTEST_EXIT=0
else
  PYTEST_EXIT=$?
  OVERALL_EXIT=1
fi

if run_with_log "mock_harness" "$MOCK_HARNESS_LOG" \
  ./scripts/run-integration-harness.sh --mode mock --env-file "$ENV_FILE" --artifacts-dir "$MOCK_ARTIFACTS_DIR"; then
  MOCK_EXIT=0
else
  MOCK_EXIT=$?
  OVERALL_EXIT=1
fi

if [[ $INCLUDE_REAL_TESTNET -eq 1 ]]; then
  mkdir -p "$REAL_ARTIFACTS_DIR"
  if [[ "${HEDERA_SHIELD_ENABLE_REAL_TESTNET:-0}" != "1" ]]; then
    REAL_EXIT=1
    REAL_EVIDENCE_EXIT=1
    OVERALL_EXIT=1
    emit "real_opt_in" "FAIL" "set HEDERA_SHIELD_ENABLE_REAL_TESTNET=1 when using --include-real-testnet"
  else
    emit "real_opt_in" "PASS" "explicit real testnet opt-in enabled"

    if run_with_log "real_harness" "$REAL_HARNESS_LOG" \
      ./scripts/run-integration-harness.sh --mode real --env-file "$ENV_FILE" --artifacts-dir "$REAL_ARTIFACTS_DIR"; then
      REAL_EXIT=0
    else
      REAL_EXIT=$?
      OVERALL_EXIT=1
    fi

    if run_with_log "real_evidence" "$REAL_EVIDENCE_LOG" \
      ./scripts/capture-testnet-evidence.sh --env-file "$ENV_FILE" --output "$REAL_ARTIFACTS_DIR/TESTNET_EVIDENCE.md" --limit 5; then
      REAL_EVIDENCE_EXIT=0
    else
      REAL_EVIDENCE_EXIT=$?
      OVERALL_EXIT=1
    fi
  fi
else
  emit "real_testnet" "SKIP" "pass --include-real-testnet plus HEDERA_SHIELD_ENABLE_REAL_TESTNET=1 to include live artifacts"
fi

if run_with_log "package_submission" "$PACKAGE_LOG" ./scripts/package-submission.sh; then
  PACKAGE_EXIT=0
else
  PACKAGE_EXIT=$?
  OVERALL_EXIT=1
fi

if [[ $PACKAGE_EXIT -eq 0 ]]; then
  tar -czf "$RELEASE_TAR_GZ" -C "$ROOT_DIR" "${SUBMISSION_ZIP#"$ROOT_DIR/"}" "${RELEASE_DIR#"$ROOT_DIR/"}" > /dev/null 2>&1
  TAR_EXIT=$?
  if [[ $TAR_EXIT -eq 0 ]]; then
    emit "release_bundle" "PASS" "created $RELEASE_TAR_GZ"
  else
    OVERALL_EXIT=1
    emit "release_bundle" "FAIL" "failed to create $RELEASE_TAR_GZ"
  fi
else
  TAR_EXIT="SKIP"
  emit "release_bundle" "SKIP" "submission bundle was not created"
fi

cat > "$REPORT_MD" <<REPORT
# HederaShield Release Evidence

- Timestamp (UTC): $TIMESTAMP_UTC
- Env file: $ENV_FILE
- Overall: $(status_for_exit "$OVERALL_EXIT")

## Step Results
- lint: $(status_for_exit "$LINT_EXIT") (exit $LINT_EXIT)
- pytest: $(status_for_exit "$PYTEST_EXIT") (exit $PYTEST_EXIT)
- mock_harness: $(status_for_exit "$MOCK_EXIT") (exit $MOCK_EXIT)
- real_harness: $(status_for_exit "$REAL_EXIT") (exit $REAL_EXIT)
- real_evidence: $(status_for_exit "$REAL_EVIDENCE_EXIT") (exit $REAL_EVIDENCE_EXIT)
- package_submission: $(status_for_exit "$PACKAGE_EXIT") (exit $PACKAGE_EXIT)
- release_bundle: $(status_for_exit "$TAR_EXIT") (exit $TAR_EXIT)

## Outputs
- Submission zip: $SUBMISSION_ZIP
- Release evidence bundle: $RELEASE_TAR_GZ
- Logs: $LOG_DIR
REPORT

python3 - "$REPORT_JSON" \
  "$TIMESTAMP_UTC" \
  "$ENV_FILE" \
  "$OVERALL_EXIT" \
  "$LINT_EXIT" \
  "$PYTEST_EXIT" \
  "$MOCK_EXIT" \
  "$REAL_EXIT" \
  "$REAL_EVIDENCE_EXIT" \
  "$PACKAGE_EXIT" \
  "$TAR_EXIT" \
  "$SUBMISSION_ZIP" \
  "$RELEASE_TAR_GZ" \
  "$RELEASE_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

path = Path(sys.argv[1])

def normalize(value: str) -> int | str:
    if value.isdigit():
        return int(value)
    return value

payload = {
    "timestamp_utc": sys.argv[2],
    "env_file": sys.argv[3],
    "overall": "PASS" if sys.argv[4] == "0" else "FAIL",
    "steps": {
        "lint": normalize(sys.argv[5]),
        "pytest": normalize(sys.argv[6]),
        "mock_harness": normalize(sys.argv[7]),
        "real_harness": normalize(sys.argv[8]),
        "real_evidence": normalize(sys.argv[9]),
        "package_submission": normalize(sys.argv[10]),
        "release_bundle": normalize(sys.argv[11]),
    },
    "outputs": {
        "submission_zip": sys.argv[12],
        "release_bundle": sys.argv[13],
        "release_dir": sys.argv[14],
    },
}

path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY

if [[ $OVERALL_EXIT -eq 0 ]]; then
  emit "summary" "PASS" "release evidence generated successfully"
else
  emit "summary" "FAIL" "one or more checks failed"
fi

exit "$OVERALL_EXIT"
