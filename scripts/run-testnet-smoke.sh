#!/usr/bin/env bash
set -u -o pipefail

ENV_FILE=".env.testnet"
SKIP_NETWORK="${HEDERA_SHIELD_SMOKE_SKIP_NETWORK:-0}"

if [[ "${1:-}" == "--skip-network" ]]; then
  SKIP_NETWORK="1"
  shift
fi

if [[ -n "${1:-}" ]]; then
  ENV_FILE="$1"
fi

FAILURES=0

emit() {
  local check="$1"
  local status="$2"
  local details="$3"
  printf 'SMOKE|%s|%s|%s\n' "$check" "$status" "$details"
}

fail() {
  local check="$1"
  local details="$2"
  FAILURES=$((FAILURES + 1))
  emit "$check" "FAIL" "$details"
}

pass() {
  local check="$1"
  local details="$2"
  emit "$check" "PASS" "$details"
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

if [[ ! -f "$ENV_FILE" ]]; then
  fail "env_file" "missing file: $ENV_FILE"
else
  pass "env_file" "found $ENV_FILE"
fi

if command -v python3 >/dev/null 2>&1; then
  pass "python3" "python3 is available"
else
  fail "python3" "python3 is required"
fi

if command -v curl >/dev/null 2>&1; then
  pass "curl" "curl is available"
else
  fail "curl" "curl is required"
fi

if [[ -f "$ENV_FILE" ]]; then
  VALIDATOR_OUTPUT="$(python3 scripts/validate-testnet-env.py "$ENV_FILE" 2>&1)"
  VALIDATOR_EXIT=$?
  if [[ $VALIDATOR_EXIT -eq 0 ]]; then
    pass "env_validation" "validator accepted $ENV_FILE"
  else
    NORMALIZED="$(printf '%s' "$VALIDATOR_OUTPUT" | tr '\n' ' ' | sed 's/[[:space:]]\+/ /g; s/[[:space:]]$//')"
    fail "env_validation" "$NORMALIZED"
  fi
fi

NETWORK=""
MIRROR_NODE_URL=""
if [[ -f "$ENV_FILE" ]]; then
  NETWORK="$(read_env_value "HEDERA_SHIELD_HEDERA_NETWORK" "$ENV_FILE")"
  MIRROR_NODE_URL="$(read_env_value "HEDERA_SHIELD_MIRROR_NODE_URL" "$ENV_FILE")"
fi

if [[ -n "$NETWORK" ]]; then
  if [[ "$NETWORK" == "testnet" ]]; then
    pass "network" "HEDERA_SHIELD_HEDERA_NETWORK=testnet"
  else
    fail "network" "expected testnet but got $NETWORK"
  fi
else
  fail "network" "HEDERA_SHIELD_HEDERA_NETWORK not found"
fi

if [[ -z "$MIRROR_NODE_URL" ]]; then
  fail "mirror_url" "HEDERA_SHIELD_MIRROR_NODE_URL not found"
else
  pass "mirror_url" "using $MIRROR_NODE_URL"
fi

if [[ "$SKIP_NETWORK" == "1" ]]; then
  pass "mirror_probe" "skipped network call"
elif [[ -n "$MIRROR_NODE_URL" ]]; then
  SUPPLY_URL="${MIRROR_NODE_URL%/}/api/v1/network/supply"
  RESPONSE="$(curl --silent --show-error --fail --max-time 20 "$SUPPLY_URL" 2>&1)"
  CURL_EXIT=$?
  if [[ $CURL_EXIT -ne 0 ]]; then
    fail "mirror_probe" "curl failed for $SUPPLY_URL: $RESPONSE"
  else
    if python3 - "$RESPONSE" <<'PY'
import json
import sys

raw = sys.argv[1]
data = json.loads(raw)
if "released_supply" not in data and "total_supply" not in data:
    raise SystemExit(1)
PY
    then
      pass "mirror_probe" "mirror node returned network supply payload"
    else
      fail "mirror_probe" "response missing released_supply/total_supply fields"
    fi
  fi
fi

if [[ "$FAILURES" -gt 0 ]]; then
  emit "summary" "FAIL" "$FAILURES checks failed"
  exit 1
fi

emit "summary" "PASS" "all checks passed"
exit 0
