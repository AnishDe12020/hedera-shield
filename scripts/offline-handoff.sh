#!/usr/bin/env bash
set -u -o pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TIMESTAMP_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT_BASE_DIR="$ROOT_DIR/artifacts/offline-handoff"
OUTPUT_DIR=""
REMOTE="origin"
BRANCH=""
SYNC_REPORT="$ROOT_DIR/dist/sync-submit-status-latest.txt"

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/offline-handoff.sh [--timestamp YYYYMMDDTHHMMSSZ] [--output-base-dir PATH] [--output-dir PATH] [--remote NAME] [--branch NAME] [--sync-report PATH]

Behavior:
  - Produces an offline handoff package for local commits not pushed upstream.
  - Writes branch/upstream/ahead-behind summary + commit list.
  - Exports git bundle + format-patch series.
  - Emits restore/apply instructions for transfer to another machine.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --timestamp)
      TIMESTAMP_UTC="${2:-}"
      shift 2
      ;;
    --output-base-dir)
      OUTPUT_BASE_DIR="${2:-}"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="${2:-}"
      shift 2
      ;;
    --remote)
      REMOTE="${2:-}"
      shift 2
      ;;
    --branch)
      BRANCH="${2:-}"
      shift 2
      ;;
    --sync-report)
      SYNC_REPORT="${2:-}"
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

emit() {
  local check="$1"
  local status="$2"
  local details="$3"
  printf 'HANDOFF|%s|%s|%s\n' "$check" "$status" "$details"
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

if [[ -z "$OUTPUT_DIR" ]]; then
  OUTPUT_DIR="$OUTPUT_BASE_DIR/$TIMESTAMP_UTC"
fi

mkdir -p "$OUTPUT_DIR"

SUMMARY_FILE="$OUTPUT_DIR/handoff-summary.txt"
STATUS_FILE="$OUTPUT_DIR/branch-status.txt"
COMMIT_LIST_FILE="$OUTPUT_DIR/commit-list.txt"
BUNDLE_FILE="$OUTPUT_DIR/offline.bundle"
PATCH_DIR="$OUTPUT_DIR/patches"
RESTORE_FILE="$OUTPUT_DIR/RESTORE_APPLY.md"

UPSTREAM_REF=""
if upstream="$(git rev-parse --abbrev-ref --symbolic-full-name "${BRANCH}@{upstream}" 2>/dev/null)"; then
  UPSTREAM_REF="$upstream"
fi

AHEAD_COUNT=0
BEHIND_COUNT=0
COMMIT_RANGE=""

if [[ -n "$UPSTREAM_REF" ]]; then
  counts="$(git rev-list --left-right --count "$UPSTREAM_REF...HEAD" 2>/dev/null || echo "0 0")"
  read -r BEHIND_COUNT AHEAD_COUNT <<< "$counts"
  COMMIT_RANGE="$UPSTREAM_REF..HEAD"
else
  AHEAD_COUNT="$(git rev-list --count HEAD 2>/dev/null || echo "0")"
  BEHIND_COUNT=0
  COMMIT_RANGE="HEAD"
fi

{
  echo "Branch: $BRANCH"
  if [[ -n "$UPSTREAM_REF" ]]; then
    echo "Upstream: $UPSTREAM_REF"
  else
    echo "Upstream: <none>"
  fi
  echo "Ahead: $AHEAD_COUNT"
  echo "Behind: $BEHIND_COUNT"
  echo "Remote: $REMOTE"
  if git remote get-url "$REMOTE" > /dev/null 2>&1; then
    echo "Remote URL: $(git remote get-url "$REMOTE")"
  else
    echo "Remote URL: <not configured>"
  fi
} > "$STATUS_FILE"

if [[ -n "$UPSTREAM_REF" ]]; then
  git log --reverse --date=iso-strict --pretty=format:'%H|%ad|%an|%s' "$COMMIT_RANGE" > "$COMMIT_LIST_FILE"
else
  git log --reverse --date=iso-strict --pretty=format:'%H|%ad|%an|%s' HEAD > "$COMMIT_LIST_FILE"
fi

BUNDLE_STATUS="SKIPPED"
PATCH_STATUS="SKIPPED"

if (( AHEAD_COUNT > 0 )); then
  if [[ -n "$UPSTREAM_REF" ]]; then
    git bundle create "$BUNDLE_FILE" "$COMMIT_RANGE"
    git format-patch --output-directory "$PATCH_DIR" --full-index --binary "$COMMIT_RANGE" > /dev/null
  else
    git bundle create "$BUNDLE_FILE" HEAD
    git format-patch --output-directory "$PATCH_DIR" --full-index --binary --root HEAD > /dev/null
  fi
  BUNDLE_STATUS="CREATED"
  PATCH_STATUS="CREATED"
fi

extract_sync_error() {
  local header="$1"
  local report="$2"
  awk -v header="$header" '
    $0 == header { in_block = 1; next }
    in_block && $0 == "" { exit }
    in_block { print }
  ' "$report"
}

SYNC_REACHABILITY_ERROR=""
SYNC_PUSH_FINAL_ERROR=""
if [[ -f "$SYNC_REPORT" ]]; then
  SYNC_REACHABILITY_ERROR="$(extract_sync_error "REMOTE_REACHABILITY_ERROR:" "$SYNC_REPORT")"
  SYNC_PUSH_FINAL_ERROR="$(extract_sync_error "PUSH_FINAL_ERROR:" "$SYNC_REPORT")"
fi

PATCH_COUNT=0
if [[ -d "$PATCH_DIR" ]]; then
  PATCH_COUNT="$(find "$PATCH_DIR" -maxdepth 1 -type f -name '*.patch' | wc -l | tr -d ' ')"
fi

{
  echo "HederaShield Offline Handoff"
  echo "Timestamp UTC: $TIMESTAMP_UTC"
  echo ""
  echo "Summary"
  echo "- Branch: $BRANCH"
  if [[ -n "$UPSTREAM_REF" ]]; then
    echo "- Upstream: $UPSTREAM_REF"
  else
    echo "- Upstream: <none>"
  fi
  echo "- Ahead: $AHEAD_COUNT"
  echo "- Behind: $BEHIND_COUNT"
  echo "- Bundle: $BUNDLE_STATUS"
  echo "- Patch series: $PATCH_STATUS ($PATCH_COUNT patches)"
  echo ""
  echo "Files"
  echo "- branch-status.txt"
  echo "- commit-list.txt"
  if [[ "$BUNDLE_STATUS" == "CREATED" ]]; then
    echo "- offline.bundle"
    echo "- patches/*.patch"
  else
    echo "- offline.bundle <not created: no unpushed commits>"
    echo "- patches/*.patch <not created: no unpushed commits>"
  fi
  echo "- RESTORE_APPLY.md"
  if [[ -n "$SYNC_REACHABILITY_ERROR" || -n "$SYNC_PUSH_FINAL_ERROR" ]]; then
    echo ""
    echo "Sync Error Context"
    if [[ -n "$SYNC_REACHABILITY_ERROR" ]]; then
      echo "REMOTE_REACHABILITY_ERROR (from $(realpath --relative-to="$ROOT_DIR" "$SYNC_REPORT")):"
      printf '%s\n' "$SYNC_REACHABILITY_ERROR"
      echo ""
    fi
    if [[ -n "$SYNC_PUSH_FINAL_ERROR" ]]; then
      echo "PUSH_FINAL_ERROR (from $(realpath --relative-to="$ROOT_DIR" "$SYNC_REPORT")):"
      printf '%s\n' "$SYNC_PUSH_FINAL_ERROR"
      echo ""
    fi
  fi
} > "$SUMMARY_FILE"

{
  echo "# Offline Restore and Apply"
  echo ""
  echo "Package directory: $(realpath --relative-to="$ROOT_DIR" "$OUTPUT_DIR")"
  echo ""
  echo "## Option 1: Restore using git bundle"
  echo "1. Copy \`offline.bundle\` to target machine."
  echo "2. In target repo:"
  echo ""
  echo "   \`\`\`bash"
  echo "   git fetch /path/to/offline.bundle \"$BRANCH\""
  echo "   git checkout -B \"$BRANCH\" FETCH_HEAD"
  echo "   \`\`\`"
  echo ""
  echo "## Option 2: Apply patch series"
  echo "1. Copy \`patches/*.patch\` to target machine."
  echo "2. In target repo on desired base branch:"
  echo ""
  echo "   \`\`\`bash"
  echo "   git am /path/to/patches/*.patch"
  echo "   \`\`\`"
  echo ""
  echo "## Validate"
  echo ""
  echo "\`\`\`bash"
  echo "git log --oneline --decorate -n 20"
  echo "git status --short --branch"
  echo "\`\`\`"
} > "$RESTORE_FILE"

emit "status" "PASS" "wrote $STATUS_FILE"
emit "commits" "PASS" "wrote $COMMIT_LIST_FILE"
if [[ "$BUNDLE_STATUS" == "CREATED" ]]; then
  emit "bundle" "PASS" "wrote $BUNDLE_FILE"
  emit "patches" "PASS" "wrote $PATCH_DIR ($PATCH_COUNT patches)"
else
  emit "bundle" "WARN" "skipped; no unpushed commits"
  emit "patches" "WARN" "skipped; no unpushed commits"
fi
emit "restore" "PASS" "wrote $RESTORE_FILE"
emit "summary" "PASS" "wrote $SUMMARY_FILE"

exit 0
