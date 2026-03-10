#!/usr/bin/env bash
set -u -o pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

REMOTE="origin"
BRANCH=""
DNS_HOST="github.com"
CHECK_INTERVAL_SECONDS=30
MAX_CHECKS=20
DRY_RUN=0
DIST_DIR="$ROOT_DIR/dist"
REPORT_FILE=""
JSON_FILE=""
EVENT_LOG=""

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/network-recovery-push-runner.sh [--remote NAME] [--branch NAME] [--dns-host HOST] [--check-interval-seconds N] [--max-checks N] [--dry-run] [--dist-dir PATH] [--report-file PATH] [--json-file PATH]

Behavior:
  - Periodically checks DNS and remote reachability.
  - Pushes pending local commits once reachable (safe push only; no force, no rebase).
  - Writes human-readable and machine-readable status artifacts.
  - Offline-safe: reports blocked state and preserves exact push/network errors.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --remote)
      REMOTE="${2:-}"
      shift 2
      ;;
    --branch)
      BRANCH="${2:-}"
      shift 2
      ;;
    --dns-host)
      DNS_HOST="${2:-}"
      shift 2
      ;;
    --check-interval-seconds)
      CHECK_INTERVAL_SECONDS="${2:-}"
      shift 2
      ;;
    --max-checks)
      MAX_CHECKS="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift 1
      ;;
    --dist-dir)
      DIST_DIR="${2:-}"
      shift 2
      ;;
    --report-file)
      REPORT_FILE="${2:-}"
      shift 2
      ;;
    --json-file)
      JSON_FILE="${2:-}"
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

if ! [[ "$CHECK_INTERVAL_SECONDS" =~ ^[0-9]+$ ]]; then
  echo "--check-interval-seconds must be a non-negative integer" >&2
  exit 2
fi
if ! [[ "$MAX_CHECKS" =~ ^[0-9]+$ ]] || (( MAX_CHECKS < 1 )); then
  echo "--max-checks must be a positive integer" >&2
  exit 2
fi

emit() {
  local check="$1"
  local status="$2"
  local details="$3"
  printf 'RECOVERY|%s|%s|%s\n' "$check" "$status" "$details"
  EVENT_LOG+="RECOVERY|$check|$status|$details\n"
}

if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  emit "git_repo" "FAIL" "current directory is not a git repository"
  exit 1
fi

if [[ -z "$BRANCH" ]]; then
  BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
fi
if [[ -z "$BRANCH" || "$BRANCH" == "HEAD" ]]; then
  emit "branch" "FAIL" "unable to determine current branch"
  exit 1
fi

if ! git remote get-url "$REMOTE" > /dev/null 2>&1; then
  emit "remote" "FAIL" "remote '$REMOTE' is not configured"
  exit 1
fi

REMOTE_URL="$(git remote get-url "$REMOTE")"
TIMESTAMP_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$DIST_DIR"
if [[ -z "$REPORT_FILE" ]]; then
  REPORT_FILE="$DIST_DIR/network-recovery-push-status-$TIMESTAMP_UTC.txt"
fi
if [[ -z "$JSON_FILE" ]]; then
  JSON_FILE="$DIST_DIR/network-recovery-push-status-$TIMESTAMP_UTC.json"
fi
mkdir -p "$(dirname "$REPORT_FILE")"
mkdir -p "$(dirname "$JSON_FILE")"
LATEST_REPORT="$DIST_DIR/network-recovery-push-status-latest.txt"
LATEST_JSON="$DIST_DIR/network-recovery-push-status-latest.json"

UPSTREAM_REF=""
if upstream="$(git rev-parse --abbrev-ref --symbolic-full-name "${BRANCH}@{upstream}" 2>/dev/null)"; then
  UPSTREAM_REF="$upstream"
fi

PUSH_STATUS="NOT_ATTEMPTED"
EXIT_CODE=1
CHECKS_RUN=0
LAST_DNS_STATUS="UNKNOWN"
LAST_REACHABLE_STATUS="UNKNOWN"
LAST_DNS_ERROR=""
LAST_REACHABILITY_ERROR=""
LAST_PUSH_ERROR=""
LAST_PENDING_COMMITS=""
AHEAD_COUNT=0
BEHIND_COUNT=0

check_dns_host() {
  local host="$1"
  if [[ -z "$host" ]]; then
    return 2
  fi

  if command -v getent > /dev/null 2>&1; then
    getent hosts "$host"
    return $?
  fi

  python3 - "$host" <<'PY'
import socket
import sys

host = sys.argv[1]
try:
    addresses = socket.getaddrinfo(host, None)
except OSError as exc:
    print(str(exc))
    sys.exit(1)

seen = []
for entry in addresses:
    addr = entry[4][0]
    if addr not in seen:
        seen.append(addr)
for addr in seen:
    print(f"{addr} {host}")
PY
}

while (( CHECKS_RUN < MAX_CHECKS )); do
  CHECKS_RUN=$((CHECKS_RUN + 1))

  if [[ -n "$UPSTREAM_REF" ]]; then
    counts="$(git rev-list --left-right --count "$UPSTREAM_REF...HEAD" 2>/dev/null || echo "0 0")"
    read -r BEHIND_COUNT AHEAD_COUNT <<< "$counts"
    LAST_PENDING_COMMITS="$(git log --oneline "$UPSTREAM_REF..HEAD" 2>/dev/null || true)"
  else
    AHEAD_COUNT="$(git rev-list --count HEAD 2>/dev/null || echo "0")"
    BEHIND_COUNT=0
    LAST_PENDING_COMMITS="$(git log --oneline -n 20 HEAD 2>/dev/null || true)"
  fi

  emit "loop" "PASS" "check $CHECKS_RUN/$MAX_CHECKS (ahead=$AHEAD_COUNT, behind=$BEHIND_COUNT)"

  if (( AHEAD_COUNT == 0 )); then
    PUSH_STATUS="NO_PENDING_COMMITS"
    LAST_DNS_STATUS="SKIP"
    LAST_REACHABLE_STATUS="SKIP"
    emit "pending_commits" "PASS" "no local commits pending push"
    EXIT_CODE=0
    break
  fi

  dns_output="$(check_dns_host "$DNS_HOST" 2>&1)"
  dns_exit=$?
  if [[ $dns_exit -eq 0 ]]; then
    LAST_DNS_STATUS="PASS"
    LAST_DNS_ERROR=""
    emit "dns" "PASS" "resolved $DNS_HOST"
  else
    LAST_DNS_STATUS="FAIL"
    LAST_DNS_ERROR="$dns_output"
    PUSH_STATUS="BLOCKED_DNS"
    emit "dns" "FAIL" "unable to resolve $DNS_HOST"
  fi

  reachability_output="$(git ls-remote --heads "$REMOTE" 2>&1)"
  reachability_exit=$?
  if [[ $reachability_exit -eq 0 ]]; then
    LAST_REACHABLE_STATUS="PASS"
    LAST_REACHABILITY_ERROR=""
    emit "remote_reachability" "PASS" "remote '$REMOTE' reachable"
  else
    LAST_REACHABLE_STATUS="FAIL"
    LAST_REACHABILITY_ERROR="$reachability_output"
    PUSH_STATUS="BLOCKED_REMOTE_UNREACHABLE"
    emit "remote_reachability" "FAIL" "remote '$REMOTE' unreachable"
  fi

  if [[ "$LAST_DNS_STATUS" != "PASS" || "$LAST_REACHABLE_STATUS" != "PASS" ]]; then
    if (( CHECKS_RUN < MAX_CHECKS )); then
      emit "wait" "WARN" "blocked by network/DNS; retrying in ${CHECK_INTERVAL_SECONDS}s"
      sleep "$CHECK_INTERVAL_SECONDS"
      continue
    fi
    EXIT_CODE=1
    break
  fi

  if (( DRY_RUN == 1 )); then
    PUSH_STATUS="DRY_RUN_PENDING"
    emit "push" "WARN" "dry-run enabled; push not executed"
    EXIT_CODE=0
    break
  fi

  push_output="$(git push "$REMOTE" "$BRANCH" 2>&1)"
  push_exit=$?
  if [[ $push_exit -eq 0 ]]; then
    PUSH_STATUS="PUSHED"
    LAST_PUSH_ERROR=""
    emit "push" "PASS" "push succeeded"
    EXIT_CODE=0
    break
  fi

  PUSH_STATUS="PUSH_FAILED"
  LAST_PUSH_ERROR="$push_output"
  emit "push" "FAIL" "push failed"

  if (( CHECKS_RUN < MAX_CHECKS )); then
    emit "wait" "WARN" "push failed; retrying in ${CHECK_INTERVAL_SECONDS}s"
    sleep "$CHECK_INTERVAL_SECONDS"
    continue
  fi

  EXIT_CODE=1
  break
done

if (( CHECKS_RUN == MAX_CHECKS )) && [[ "$PUSH_STATUS" == "NOT_ATTEMPTED" ]]; then
  PUSH_STATUS="MAX_CHECKS_REACHED"
  EXIT_CODE=1
fi

if [[ $EXIT_CODE -eq 0 ]]; then
  emit "summary" "PASS" "runner completed successfully"
else
  emit "summary" "FAIL" "runner blocked or push unsuccessful; see artifacts"
fi

{
  echo "HederaShield Network-Recovery Push Runner"
  echo "Timestamp UTC: $TIMESTAMP_UTC"
  echo "Branch: $BRANCH"
  echo "Remote: $REMOTE"
  echo "Remote URL: $REMOTE_URL"
  if [[ -n "$UPSTREAM_REF" ]]; then
    echo "Upstream: $UPSTREAM_REF"
  else
    echo "Upstream: <none>"
  fi
  echo "DNS Host: $DNS_HOST"
  echo "Dry Run: $DRY_RUN"
  echo "Check Interval Seconds: $CHECK_INTERVAL_SECONDS"
  echo "Max Checks: $MAX_CHECKS"
  echo "Checks Run: $CHECKS_RUN"
  echo ""
  echo "Summary"
  echo "- Push status: $PUSH_STATUS"
  echo "- Pending local commits: $AHEAD_COUNT"
  echo "- Behind upstream: $BEHIND_COUNT"
  echo "- DNS status: $LAST_DNS_STATUS"
  echo "- Remote reachability: $LAST_REACHABLE_STATUS"
  echo "- Exit code: $EXIT_CODE"
  echo ""
  echo "Recent Events"
  printf '%b' "$EVENT_LOG"
  echo ""
  echo "Pending Commit List"
  if [[ -n "$LAST_PENDING_COMMITS" ]]; then
    printf '%s\n' "$LAST_PENDING_COMMITS"
  else
    echo "<none>"
  fi
  echo ""
  if [[ -n "$LAST_DNS_ERROR" ]]; then
    echo "DNS_ERROR:"
    printf '%s\n' "$LAST_DNS_ERROR"
    echo ""
  fi
  if [[ -n "$LAST_REACHABILITY_ERROR" ]]; then
    echo "REMOTE_REACHABILITY_ERROR:"
    printf '%s\n' "$LAST_REACHABILITY_ERROR"
    echo ""
  fi
  if [[ -n "$LAST_PUSH_ERROR" ]]; then
    echo "PUSH_FINAL_ERROR:"
    printf '%s\n' "$LAST_PUSH_ERROR"
    echo ""
  fi

  if [[ $EXIT_CODE -ne 0 ]]; then
    echo "Actionable Next Step"
    echo "- Keep local work and rerun this runner when DNS/network recovers."
    echo "- If push keeps failing, inspect PUSH_FINAL_ERROR above for exact server response."
  fi
} > "$REPORT_FILE"

export TIMESTAMP_UTC BRANCH REMOTE REMOTE_URL UPSTREAM_REF DNS_HOST DRY_RUN CHECK_INTERVAL_SECONDS
export MAX_CHECKS CHECKS_RUN AHEAD_COUNT BEHIND_COUNT PUSH_STATUS LAST_DNS_STATUS LAST_REACHABLE_STATUS
export EXIT_CODE LAST_PENDING_COMMITS EVENT_LOG LAST_DNS_ERROR LAST_REACHABILITY_ERROR LAST_PUSH_ERROR

python3 - "$JSON_FILE" <<'PY'
import json
import os
import sys

json_file = sys.argv[1]

def _split_lines(value: str) -> list[str]:
    if not value:
        return []
    return [line for line in value.splitlines() if line.strip()]

payload = {
    "timestamp_utc": os.environ.get("TIMESTAMP_UTC", ""),
    "branch": os.environ.get("BRANCH", ""),
    "remote": os.environ.get("REMOTE", ""),
    "remote_url": os.environ.get("REMOTE_URL", ""),
    "upstream": os.environ.get("UPSTREAM_REF", ""),
    "dns_host": os.environ.get("DNS_HOST", ""),
    "dry_run": os.environ.get("DRY_RUN", "0") == "1",
    "check_interval_seconds": int(os.environ.get("CHECK_INTERVAL_SECONDS", "0")),
    "max_checks": int(os.environ.get("MAX_CHECKS", "0")),
    "checks_run": int(os.environ.get("CHECKS_RUN", "0")),
    "ahead_count": int(os.environ.get("AHEAD_COUNT", "0")),
    "behind_count": int(os.environ.get("BEHIND_COUNT", "0")),
    "push_status": os.environ.get("PUSH_STATUS", ""),
    "dns_status": os.environ.get("LAST_DNS_STATUS", ""),
    "remote_reachability_status": os.environ.get("LAST_REACHABLE_STATUS", ""),
    "exit_code": int(os.environ.get("EXIT_CODE", "1")),
    "blocked": os.environ.get("EXIT_CODE", "1") != "0",
    "pending_commits": _split_lines(os.environ.get("LAST_PENDING_COMMITS", "")),
    "events": _split_lines(os.environ.get("EVENT_LOG", "")),
    "errors": {
        "dns": os.environ.get("LAST_DNS_ERROR", ""),
        "remote_reachability": os.environ.get("LAST_REACHABILITY_ERROR", ""),
        "push": os.environ.get("LAST_PUSH_ERROR", ""),
    },
}

with open(json_file, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=2)
    handle.write("\n")
PY

cp "$REPORT_FILE" "$LATEST_REPORT"
cp "$JSON_FILE" "$LATEST_JSON"
emit "report" "PASS" "wrote $REPORT_FILE"
emit "report_json" "PASS" "wrote $JSON_FILE"
emit "report_latest" "PASS" "updated $LATEST_REPORT"
emit "report_json_latest" "PASS" "updated $LATEST_JSON"

exit "$EXIT_CODE"
