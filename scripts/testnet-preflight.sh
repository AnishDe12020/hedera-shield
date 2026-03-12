#!/usr/bin/env bash
set -u -o pipefail

ENV_FILE=".env.testnet"
TIMEOUT_SECONDS=8
ALLOW_YELLOW=0

usage() {
  cat <<'EOF'
Usage:
  ./scripts/testnet-preflight.sh [--env-file FILE] [--timeout-seconds N] [--allow-yellow]

Wrapper around scripts/integration_preflight.sh for integration go/no-go:
- default: PASS only when OVERALL READINESS is GREEN
- --allow-yellow: PASS when GREEN or YELLOW
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      ENV_FILE="${2:-}"
      shift 2
      ;;
    --timeout-seconds)
      TIMEOUT_SECONDS="${2:-}"
      shift 2
      ;;
    --allow-yellow)
      ALLOW_YELLOW=1
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

if [[ ! -x "./scripts/integration_preflight.sh" ]]; then
  echo "PREFLIGHT|wrapper|FAIL|missing executable scripts/integration_preflight.sh"
  exit 2
fi

set +e
OUTPUT="$("./scripts/integration_preflight.sh" --env-file "$ENV_FILE" --timeout-seconds "$TIMEOUT_SECONDS" 2>&1)"
INNER_EXIT=$?
set -e

printf '%s\n' "$OUTPUT"

OVERALL_LINE="$(printf '%s\n' "$OUTPUT" | grep -E 'OVERALL READINESS: ' | tail -n 1 || true)"
OVERALL="${OVERALL_LINE##*: }"
OVERALL="${OVERALL//[$'\r\n']}"

if [[ "$OVERALL" == "GREEN" ]]; then
  echo "PREFLIGHT|overall|PASS|overall readiness is GREEN"
  echo "PREFLIGHT|summary|PASS|integration preflight gate passed"
  exit 0
fi

if [[ "$OVERALL" == "YELLOW" && "$ALLOW_YELLOW" -eq 1 ]]; then
  echo "PREFLIGHT|overall|PASS|overall readiness is YELLOW and --allow-yellow enabled"
  echo "PREFLIGHT|summary|PASS|integration preflight gate passed with caution"
  exit 0
fi

if [[ -z "$OVERALL" ]]; then
  echo "PREFLIGHT|overall|FAIL|could not parse OVERALL READINESS line (inner exit=$INNER_EXIT)"
else
  echo "PREFLIGHT|overall|FAIL|overall readiness is $OVERALL"
fi
echo "PREFLIGHT|summary|FAIL|integration preflight gate failed"
exit 1
