#!/usr/bin/env bash
set -u -o pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DEMO_ID="3min-offline"
DEMO_DIR="$ROOT_DIR/artifacts/demo/$DEMO_ID"
DIST_DIR="$ROOT_DIR/dist"
INTEGRATION_ARTIFACTS_DIR="$ROOT_DIR/artifacts/integration"
REPORT_FILE=""

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/submission-readiness.sh [--demo-id NAME] [--demo-dir PATH] [--dist-dir PATH] [--integration-artifacts-dir PATH] [--report-file PATH]

Checks:
  - Required docs and checklists exist.
  - Demo artifacts required by docs/FINAL_SUBMISSION_CHECKLIST.md exist.
  - Submission bundle and release evidence artifacts exist.
  - Emits pass/fail summary and writes report to dist/ by default.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --demo-id)
      DEMO_ID="${2:-}"
      DEMO_DIR="$ROOT_DIR/artifacts/demo/$DEMO_ID"
      shift 2
      ;;
    --demo-dir)
      DEMO_DIR="${2:-}"
      shift 2
      ;;
    --dist-dir)
      DIST_DIR="${2:-}"
      shift 2
      ;;
    --integration-artifacts-dir)
      INTEGRATION_ARTIFACTS_DIR="${2:-}"
      shift 2
      ;;
    --report-file)
      REPORT_FILE="${2:-}"
      shift 2
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

TIMESTAMP_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$DIST_DIR"
if [[ -z "$REPORT_FILE" ]]; then
  REPORT_FILE="$DIST_DIR/submission-readiness-$TIMESTAMP_UTC.txt"
fi
LATEST_REPORT="$DIST_DIR/submission-readiness-latest.txt"

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0
RESULT_LINES=()

emit() {
  local check="$1"
  local status="$2"
  local details="$3"
  RESULT_LINES+=("READINESS|$check|$status|$details")
  printf 'READINESS|%s|%s|%s\n' "$check" "$status" "$details"
  case "$status" in
    PASS) PASS_COUNT=$((PASS_COUNT + 1)) ;;
    FAIL) FAIL_COUNT=$((FAIL_COUNT + 1)) ;;
    WARN) WARN_COUNT=$((WARN_COUNT + 1)) ;;
  esac
}

check_file() {
  local check_name="$1"
  local path="$2"
  if [[ -f "$path" ]]; then
    emit "$check_name" "PASS" "found ${path#"$ROOT_DIR/"}"
  else
    emit "$check_name" "FAIL" "missing ${path#"$ROOT_DIR/"}"
  fi
}

check_dir() {
  local check_name="$1"
  local path="$2"
  if [[ -d "$path" ]]; then
    emit "$check_name" "PASS" "found ${path#"$ROOT_DIR/"}/"
  else
    emit "$check_name" "FAIL" "missing ${path#"$ROOT_DIR/"}/"
  fi
}

# Required docs
check_file "doc_submission" "$ROOT_DIR/SUBMISSION.md"
check_file "doc_readme" "$ROOT_DIR/README.md"
check_file "doc_testnet_setup" "$ROOT_DIR/docs/TESTNET_SETUP.md"
check_file "doc_testnet_evidence" "$ROOT_DIR/docs/TESTNET_EVIDENCE.md"
check_file "doc_deploy_proof" "$ROOT_DIR/docs/DEPLOY_PROOF.md"
check_file "doc_demo_runbook" "$ROOT_DIR/docs/DEMO_RECORDING_RUNBOOK.md"
check_file "doc_final_checklist" "$ROOT_DIR/docs/FINAL_SUBMISSION_CHECKLIST.md"

# Demo/checklist artifacts
check_dir "demo_dir" "$DEMO_DIR"
check_dir "demo_harness_dir" "$DEMO_DIR/harness"
check_file "demo_harness_report_md" "$DEMO_DIR/harness/report.md"
check_file "demo_harness_report_json" "$DEMO_DIR/harness/report.json"
check_file "demo_harness_log" "$DEMO_DIR/harness/harness.log"
check_file "demo_smoke_log" "$DEMO_DIR/harness/smoke.log"
check_file "demo_validator_log" "$DEMO_DIR/harness/validator.log"
check_file "demo_bundle_sha256" "$DEMO_DIR/submission-bundle.zip.sha256"

# Bundles/evidence
check_file "submission_bundle" "$DIST_DIR/submission-bundle.zip"

if compgen -G "$DIST_DIR/release-evidence-*.tar.gz" > /dev/null; then
  latest_release_bundle="$(ls -1 "$DIST_DIR"/release-evidence-*.tar.gz | sort | tail -n1)"
  emit "release_bundle" "PASS" "found ${latest_release_bundle#"$ROOT_DIR/"}"
else
  emit "release_bundle" "FAIL" "missing dist/release-evidence-*.tar.gz"
fi

if [[ -d "$INTEGRATION_ARTIFACTS_DIR" ]] && compgen -G "$INTEGRATION_ARTIFACTS_DIR/release-*/release-report.md" > /dev/null; then
  latest_release_dir="$(ls -1d "$INTEGRATION_ARTIFACTS_DIR"/release-* | sort | tail -n1)"
  emit "integration_release_report_md" "PASS" "found ${latest_release_dir#"$ROOT_DIR/"}/release-report.md"
  if [[ -f "$latest_release_dir/release-report.json" ]]; then
    emit "integration_release_report_json" "PASS" "found ${latest_release_dir#"$ROOT_DIR/"}/release-report.json"
  else
    emit "integration_release_report_json" "FAIL" "missing ${latest_release_dir#"$ROOT_DIR/"}/release-report.json"
  fi
else
  emit "integration_release_report_md" "FAIL" "missing artifacts/integration/release-*/release-report.md"
  emit "integration_release_report_json" "FAIL" "missing artifacts/integration/release-*/release-report.json"
fi

summary_status="PASS"
if (( FAIL_COUNT > 0 )); then
  summary_status="FAIL"
fi

{
  echo "HederaShield Submission Readiness"
  echo "Timestamp UTC: $TIMESTAMP_UTC"
  echo "Demo ID: $DEMO_ID"
  echo "Demo dir: $DEMO_DIR"
  echo "Dist dir: $DIST_DIR"
  echo ""
  echo "Summary"
  echo "- Overall: $summary_status"
  echo "- PASS: $PASS_COUNT"
  echo "- FAIL: $FAIL_COUNT"
  echo "- WARN: $WARN_COUNT"
  echo ""
  echo "Checks"
  for line in "${RESULT_LINES[@]}"; do
    printf '%s\n' "$line"
  done

  if (( FAIL_COUNT > 0 )); then
    echo ""
    echo "Actionable Next Step"
    echo "- Run docs/DEMO_RECORDING_RUNBOOK.md commands to regenerate missing demo artifacts."
    echo "- Run ./scripts/release-evidence.sh to regenerate dist/ and artifacts/integration release outputs."
  fi
} > "$REPORT_FILE"

cp "$REPORT_FILE" "$LATEST_REPORT"
emit "report" "PASS" "wrote $REPORT_FILE"
emit "report_latest" "PASS" "updated $LATEST_REPORT"

if (( FAIL_COUNT == 0 )); then
  emit "summary" "PASS" "submission readiness checks passed"
  exit 0
fi

emit "summary" "FAIL" "submission readiness checks failed"
exit 1
