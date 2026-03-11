#!/usr/bin/env bash
set -u -o pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

REMOTE="origin"
BRANCH=""
MAX_RETRIES=3
INITIAL_BACKOFF_SECONDS=2
MAX_BACKOFF_SECONDS=16
DIST_DIR="$ROOT_DIR/dist"
REPORT_FILE=""
PUSH_STATUS_FILE="$ROOT_DIR/PUSH_STATUS.md"

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/sync-and-submit.sh [--remote NAME] [--branch NAME] [--max-retries N] [--initial-backoff-seconds N] [--max-backoff-seconds N] [--report-file PATH] [--push-status-file PATH]

Behavior:
  - Computes pending local commits versus upstream.
  - Checks remote reachability with git ls-remote.
  - Retries git push with bounded exponential backoff.
  - Writes a clear status report to dist/ by default.
  - Writes PUSH_STATUS.md with exact error output when push is blocked/failed.
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
    --max-retries)
      MAX_RETRIES="${2:-}"
      shift 2
      ;;
    --initial-backoff-seconds)
      INITIAL_BACKOFF_SECONDS="${2:-}"
      shift 2
      ;;
    --max-backoff-seconds)
      MAX_BACKOFF_SECONDS="${2:-}"
      shift 2
      ;;
    --report-file)
      REPORT_FILE="${2:-}"
      shift 2
      ;;
    --push-status-file)
      PUSH_STATUS_FILE="${2:-}"
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

if ! [[ "$MAX_RETRIES" =~ ^[0-9]+$ ]] || (( MAX_RETRIES < 1 )); then
  echo "--max-retries must be a positive integer" >&2
  exit 2
fi
if ! [[ "$INITIAL_BACKOFF_SECONDS" =~ ^[0-9]+$ ]]; then
  echo "--initial-backoff-seconds must be a non-negative integer" >&2
  exit 2
fi
if ! [[ "$MAX_BACKOFF_SECONDS" =~ ^[0-9]+$ ]] || (( MAX_BACKOFF_SECONDS < 1 )); then
  echo "--max-backoff-seconds must be a positive integer" >&2
  exit 2
fi

if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  echo "SYNC|git_repo|FAIL|current directory is not a git repository"
  exit 1
fi

if [[ -z "$BRANCH" ]]; then
  BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
fi
if [[ -z "$BRANCH" || "$BRANCH" == "HEAD" ]]; then
  echo "SYNC|branch|FAIL|unable to determine current branch"
  exit 1
fi

if ! git remote get-url "$REMOTE" > /dev/null 2>&1; then
  echo "SYNC|remote|FAIL|remote '$REMOTE' is not configured"
  exit 1
fi
REMOTE_URL="$(git remote get-url "$REMOTE")"

TIMESTAMP_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$DIST_DIR"
if [[ -z "$REPORT_FILE" ]]; then
  REPORT_FILE="$DIST_DIR/sync-submit-status-$TIMESTAMP_UTC.txt"
fi
mkdir -p "$(dirname "$REPORT_FILE")"
LATEST_REPORT="$DIST_DIR/sync-submit-status-latest.txt"

emit() {
  local check="$1"
  local status="$2"
  local details="$3"
  printf 'SYNC|%s|%s|%s\n' "$check" "$status" "$details"
}

UPSTREAM_REF=""
if upstream="$(git rev-parse --abbrev-ref --symbolic-full-name "${BRANCH}@{upstream}" 2>/dev/null)"; then
  UPSTREAM_REF="$upstream"
fi

AHEAD_COUNT=0
BEHIND_COUNT=0
PENDING_COMMITS=""
if [[ -n "$UPSTREAM_REF" ]]; then
  counts="$(git rev-list --left-right --count "$UPSTREAM_REF...HEAD" 2>/dev/null || echo "0 0")"
  read -r BEHIND_COUNT AHEAD_COUNT <<< "$counts"
  PENDING_COMMITS="$(git log --oneline "$UPSTREAM_REF..HEAD" 2>/dev/null || true)"
else
  AHEAD_COUNT="$(git rev-list --count HEAD 2>/dev/null || echo "0")"
  BEHIND_COUNT=0
  PENDING_COMMITS="$(git log --oneline -n 20 HEAD 2>/dev/null || true)"
fi

PUSH_STATUS="SKIP"
REACHABLE_STATUS="FAIL"
REACHABILITY_ERROR=""
PUSH_ERROR=""
PUSH_ATTEMPT_LOG=""

reachability_output="$(git ls-remote --heads "$REMOTE" 2>&1)"
reachability_exit=$?
if [[ $reachability_exit -eq 0 ]]; then
  REACHABLE_STATUS="PASS"
  emit "remote_reachability" "PASS" "remote '$REMOTE' reachable"
else
  REACHABILITY_ERROR="$reachability_output"
  if (( AHEAD_COUNT > 0 )); then
    emit "remote_reachability" "FAIL" "remote '$REMOTE' unreachable; push skipped"
  else
    emit "remote_reachability" "WARN" "remote '$REMOTE' unreachable but no pending commits"
  fi
fi

if (( AHEAD_COUNT == 0 )); then
  PUSH_STATUS="NO_PENDING_COMMITS"
  emit "pending_commits" "PASS" "no local commits pending push"
elif [[ "$REACHABLE_STATUS" != "PASS" ]]; then
  PUSH_STATUS="SKIPPED_UNREACHABLE"
  emit "pending_commits" "WARN" "$AHEAD_COUNT local commits pending push"
else
  backoff="$INITIAL_BACKOFF_SECONDS"
  attempt=1
  while (( attempt <= MAX_RETRIES )); do
    push_output="$(git push "$REMOTE" "$BRANCH" 2>&1)"
    push_exit=$?

    PUSH_ATTEMPT_LOG+="Attempt $attempt/$MAX_RETRIES exit=$push_exit\n$push_output\n\n"

    if [[ $push_exit -eq 0 ]]; then
      PUSH_STATUS="PUSHED"
      emit "push" "PASS" "push succeeded on attempt $attempt"
      break
    fi

    PUSH_ERROR="$push_output"
    if (( attempt == MAX_RETRIES )); then
      PUSH_STATUS="FAILED_AFTER_RETRIES"
      emit "push" "FAIL" "push failed after $MAX_RETRIES attempts"
      break
    fi

    emit "push" "WARN" "attempt $attempt failed; retrying in ${backoff}s"
    sleep "$backoff"
    backoff=$(( backoff * 2 ))
    if (( backoff > MAX_BACKOFF_SECONDS )); then
      backoff=$MAX_BACKOFF_SECONDS
    fi
    attempt=$(( attempt + 1 ))
  done
fi

{
  echo "HederaShield Sync + Submit Status"
  echo "Timestamp UTC: $TIMESTAMP_UTC"
  echo "Branch: $BRANCH"
  echo "Remote: $REMOTE"
  echo "Remote URL: $REMOTE_URL"
  if [[ -n "$UPSTREAM_REF" ]]; then
    echo "Upstream: $UPSTREAM_REF"
  else
    echo "Upstream: <none>"
  fi
  echo ""
  echo "Summary"
  echo "- Remote reachability: $REACHABLE_STATUS"
  echo "- Pending local commits: $AHEAD_COUNT"
  echo "- Behind upstream: $BEHIND_COUNT"
  echo "- Push status: $PUSH_STATUS"
  echo ""
  echo "Pending Commit List"
  if [[ -n "$PENDING_COMMITS" ]]; then
    printf '%s\n' "$PENDING_COMMITS"
  else
    echo "<none>"
  fi
  echo ""

  if [[ -n "$REACHABILITY_ERROR" ]]; then
    echo "REMOTE_REACHABILITY_ERROR:"
    printf '%s\n' "$REACHABILITY_ERROR"
    echo ""
  fi

  if [[ -n "$PUSH_ATTEMPT_LOG" ]]; then
    echo "PUSH_ATTEMPTS:"
    printf '%b' "$PUSH_ATTEMPT_LOG"
    echo ""
  fi

  if [[ -n "$PUSH_ERROR" ]]; then
    echo "PUSH_FINAL_ERROR:"
    printf '%s\n' "$PUSH_ERROR"
    echo ""
  fi

  if [[ "$PUSH_STATUS" == "SKIPPED_UNREACHABLE" || "$PUSH_STATUS" == "FAILED_AFTER_RETRIES" ]]; then
    echo "Actionable Next Step"
    echo "- Keep working locally; rerun this script once remote/DNS recovers."
    echo "- Pending commits are listed above and remain only in your local branch."
  fi
} > "$REPORT_FILE"

cp "$REPORT_FILE" "$LATEST_REPORT"
emit "report" "PASS" "wrote $REPORT_FILE"
emit "report_latest" "PASS" "updated $LATEST_REPORT"

write_push_status_failure() {
  local failure_context=""
  if [[ -n "$PUSH_ERROR" ]]; then
    failure_context="$PUSH_ERROR"
  elif [[ -n "$REACHABILITY_ERROR" ]]; then
    failure_context="$REACHABILITY_ERROR"
  else
    failure_context="No git stderr/stdout was captured."
  fi

  mkdir -p "$(dirname "$PUSH_STATUS_FILE")"
  {
    echo "# Push Failure Status"
    echo ""
    echo "- Timestamp UTC: $TIMESTAMP_UTC"
    echo "- Branch: $BRANCH"
    echo "- Remote: $REMOTE"
    echo "- Remote URL: $REMOTE_URL"
    echo "- Push status: $PUSH_STATUS"
    echo "- Pending local commits: $AHEAD_COUNT"
    echo ""
    echo "## Exact Error"
    echo '```text'
    printf '%s\n' "$failure_context"
    echo '```'
  } > "$PUSH_STATUS_FILE"
  emit "push_status_file" "PASS" "wrote $PUSH_STATUS_FILE"
}

if [[ "$PUSH_STATUS" == "PUSHED" || "$PUSH_STATUS" == "NO_PENDING_COMMITS" ]]; then
  if [[ -f "$PUSH_STATUS_FILE" ]]; then
    rm -f "$PUSH_STATUS_FILE"
    emit "push_status_file" "PASS" "removed stale $PUSH_STATUS_FILE"
  fi
  emit "summary" "PASS" "sync state is clean"
  exit 0
fi

write_push_status_failure
emit "summary" "FAIL" "sync incomplete; see $REPORT_FILE"
exit 1
