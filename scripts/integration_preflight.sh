#!/usr/bin/env bash
set -u -o pipefail

ENV_FILE=".env.testnet"
TIMEOUT_SECONDS=8

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/integration_preflight.sh [--env-file FILE] [--timeout-seconds N]

Checks integration readiness without requiring private credentials to be valid for signing:
- Required env var presence
- Hedera config format validation (network/operator/key/url/json)
- Endpoint reachability (mirror node + optional local API health)

Exit codes:
- 0: GREEN (ready)
- 1: YELLOW (proceed with caution)
- 2: RED (blocked)
USAGE
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

if ! [[ "$TIMEOUT_SECONDS" =~ ^[0-9]+$ ]] || [[ "$TIMEOUT_SECONDS" -lt 1 ]]; then
  echo "Invalid --timeout-seconds value: $TIMEOUT_SECONDS" >&2
  exit 2
fi

RED_COUNT=0
YELLOW_COUNT=0
GREEN_COUNT=0

COLOR_RED=""
COLOR_YELLOW=""
COLOR_GREEN=""
COLOR_RESET=""
if [[ -t 1 ]]; then
  COLOR_RED="$(printf '\033[31m')"
  COLOR_YELLOW="$(printf '\033[33m')"
  COLOR_GREEN="$(printf '\033[32m')"
  COLOR_RESET="$(printf '\033[0m')"
fi

RESULT_LINES=()

record_result() {
  local level="$1"
  local check="$2"
  local detail="$3"

  case "$level" in
    RED)
      RED_COUNT=$((RED_COUNT + 1))
      RESULT_LINES+=("RED|$check|$detail")
      ;;
    YELLOW)
      YELLOW_COUNT=$((YELLOW_COUNT + 1))
      RESULT_LINES+=("YELLOW|$check|$detail")
      ;;
    GREEN)
      GREEN_COUNT=$((GREEN_COUNT + 1))
      RESULT_LINES+=("GREEN|$check|$detail")
      ;;
    *)
      echo "internal error: unknown level $level" >&2
      exit 2
      ;;
  esac
}

read_env_value() {
  local key="$1"
  local file="$2"

  if [[ -n "${!key:-}" ]]; then
    printf '%s' "${!key}"
    return 0
  fi

  if [[ ! -f "$file" ]]; then
    return 1
  fi

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

is_placeholder() {
  local value="$1"
  [[ "$value" == *"YOUR_"* ]] || [[ "$value" == "" ]] || [[ "$value" == "<"*">" ]] || [[ "$value" == *"PLACEHOLDER"* ]] || [[ "$value" == *"EXAMPLE"* ]]
}

ACCOUNT_ID_RE='^[0-9]+\.[0-9]+\.[0-9]+$'
HEX_KEY_RE='^(0x)?[0-9a-fA-F]{64,128}$'
NETWORK_RE='^(testnet|mainnet|previewnet)$'
URL_RE='^https?://'

REQUIRED_VARS=(
  HEDERA_SHIELD_HEDERA_NETWORK
  HEDERA_SHIELD_HEDERA_OPERATOR_ID
  HEDERA_SHIELD_HEDERA_OPERATOR_KEY
  HEDERA_SHIELD_MIRROR_NODE_URL
  HEDERA_SHIELD_MIRROR_NODE_POLL_INTERVAL
  HEDERA_SHIELD_API_HOST
  HEDERA_SHIELD_API_PORT
  HEDERA_SHIELD_MONITORED_TOKEN_IDS
  HEDERA_SHIELD_SANCTIONED_ADDRESSES
)

OPTIONAL_WARN_VARS=(
  HEDERA_SHIELD_ANTHROPIC_API_KEY
  HEDERA_SHIELD_AI_MODEL
)

declare -A ENV_MAP

if [[ -f "$ENV_FILE" ]]; then
  record_result "GREEN" "env_file" "found $ENV_FILE"
else
  record_result "YELLOW" "env_file" "$ENV_FILE not found; using only exported environment variables"
fi

for var in "${REQUIRED_VARS[@]}"; do
  value="$(read_env_value "$var" "$ENV_FILE" || true)"
  ENV_MAP["$var"]="$value"
  if [[ -z "$value" ]]; then
    record_result "RED" "$var" "missing"
  else
    record_result "GREEN" "$var" "present"
  fi
done

for var in "${OPTIONAL_WARN_VARS[@]}"; do
  value="$(read_env_value "$var" "$ENV_FILE" || true)"
  ENV_MAP["$var"]="$value"
  if [[ -z "$value" ]] || is_placeholder "$value"; then
    record_result "YELLOW" "$var" "missing or placeholder (AI analysis fallback mode expected)"
  else
    record_result "GREEN" "$var" "present"
  fi
done

network="${ENV_MAP[HEDERA_SHIELD_HEDERA_NETWORK]:-}"
if [[ -n "$network" ]]; then
  if [[ "$network" =~ $NETWORK_RE ]]; then
    if [[ "$network" == "testnet" ]]; then
      record_result "GREEN" "network_format" "testnet"
    else
      record_result "YELLOW" "network_format" "$network (first live integration runbook expects testnet)"
    fi
  else
    record_result "RED" "network_format" "must be one of testnet/mainnet/previewnet"
  fi
fi

operator_id="${ENV_MAP[HEDERA_SHIELD_HEDERA_OPERATOR_ID]:-}"
if [[ -n "$operator_id" ]]; then
  if [[ "$operator_id" =~ $ACCOUNT_ID_RE ]]; then
    if [[ "$operator_id" == "0.0.0" ]]; then
      record_result "YELLOW" "operator_id_format" "0.0.0 looks like placeholder"
    else
      record_result "GREEN" "operator_id_format" "valid account id format"
    fi
  elif is_placeholder "$operator_id"; then
    record_result "YELLOW" "operator_id_format" "placeholder value detected"
  else
    record_result "RED" "operator_id_format" "invalid format (expected 0.0.x)"
  fi
fi

operator_key="${ENV_MAP[HEDERA_SHIELD_HEDERA_OPERATOR_KEY]:-}"
if [[ -n "$operator_key" ]]; then
  if is_placeholder "$operator_key"; then
    record_result "YELLOW" "operator_key_format" "placeholder key detected"
  elif [[ "$operator_key" =~ $HEX_KEY_RE ]]; then
    record_result "GREEN" "operator_key_format" "hex key format accepted"
  elif [[ "${#operator_key}" -ge 40 ]] && [[ "$operator_key" =~ ^[A-Za-z0-9+/=]+$ ]]; then
    record_result "GREEN" "operator_key_format" "base64-like key format accepted"
  else
    record_result "RED" "operator_key_format" "unrecognized key format"
  fi
fi

poll_interval="${ENV_MAP[HEDERA_SHIELD_MIRROR_NODE_POLL_INTERVAL]:-}"
if [[ -n "$poll_interval" ]]; then
  if [[ "$poll_interval" =~ ^[0-9]+$ ]] && [[ "$poll_interval" -gt 0 ]]; then
    record_result "GREEN" "poll_interval_format" "${poll_interval}s"
  else
    record_result "RED" "poll_interval_format" "must be positive integer"
  fi
fi

api_port="${ENV_MAP[HEDERA_SHIELD_API_PORT]:-}"
if [[ -n "$api_port" ]]; then
  if [[ "$api_port" =~ ^[0-9]+$ ]] && [[ "$api_port" -ge 1 ]] && [[ "$api_port" -le 65535 ]]; then
    record_result "GREEN" "api_port_format" "$api_port"
  else
    record_result "RED" "api_port_format" "must be integer in 1-65535"
  fi
fi

mirror_url="${ENV_MAP[HEDERA_SHIELD_MIRROR_NODE_URL]:-}"
if [[ -n "$mirror_url" ]]; then
  if [[ "$mirror_url" =~ $URL_RE ]]; then
    record_result "GREEN" "mirror_url_format" "$mirror_url"
  else
    record_result "RED" "mirror_url_format" "must start with http:// or https://"
  fi
fi

json_array_check() {
  local key="$1"
  local raw="$2"
  if [[ -z "$raw" ]]; then
    return 0
  fi

  if python3 - "$raw" <<'PY'
import json
import sys

raw = sys.argv[1]
obj = json.loads(raw)
if not isinstance(obj, list):
    raise SystemExit(1)
for item in obj:
    if not isinstance(item, str):
        raise SystemExit(1)
PY
  then
    record_result "GREEN" "${key}_format" "valid JSON string array"
  else
    record_result "RED" "${key}_format" "must be JSON array of strings"
  fi
}

json_array_check "monitored_token_ids" "${ENV_MAP[HEDERA_SHIELD_MONITORED_TOKEN_IDS]:-}"
json_array_check "sanctioned_addresses" "${ENV_MAP[HEDERA_SHIELD_SANCTIONED_ADDRESSES]:-}"

if command -v curl >/dev/null 2>&1; then
  record_result "GREEN" "curl_binary" "available"
else
  record_result "RED" "curl_binary" "not found"
fi

if command -v python3 >/dev/null 2>&1; then
  record_result "GREEN" "python3_binary" "available"
else
  record_result "RED" "python3_binary" "not found"
fi

if [[ -n "$mirror_url" ]] && [[ "$mirror_url" =~ $URL_RE ]] && command -v curl >/dev/null 2>&1; then
  mirror_supply_url="${mirror_url%/}/api/v1/network/supply"
  mirror_out="$(curl --silent --show-error --max-time "$TIMEOUT_SECONDS" "$mirror_supply_url" 2>&1 || true)"
  if [[ -z "$mirror_out" ]]; then
    record_result "RED" "mirror_reachability" "empty response from $mirror_supply_url"
  elif python3 - "$mirror_out" <<'PY'
import json
import sys

raw = sys.argv[1]
try:
    obj = json.loads(raw)
except Exception:
    raise SystemExit(1)
if not isinstance(obj, dict):
    raise SystemExit(1)
if "released_supply" not in obj and "total_supply" not in obj:
    raise SystemExit(1)
PY
  then
    record_result "GREEN" "mirror_reachability" "reachable: $mirror_supply_url"
  else
    snippet="$(printf '%s' "$mirror_out" | tr '\n' ' ' | sed 's/[[:space:]]\+/ /g' | cut -c1-140)"
    record_result "RED" "mirror_reachability" "unexpected response from $mirror_supply_url (${snippet})"
  fi
fi

api_host="${ENV_MAP[HEDERA_SHIELD_API_HOST]:-}"
if [[ -n "$api_host" ]] && [[ -n "$api_port" ]] && command -v curl >/dev/null 2>&1; then
  probe_host="$api_host"
  if [[ "$probe_host" == "0.0.0.0" ]]; then
    probe_host="127.0.0.1"
  fi
  local_health_url="http://${probe_host}:${api_port}/health"
  local_out="$(curl --silent --show-error --max-time 2 "$local_health_url" 2>&1 || true)"
  if python3 - "$local_out" <<'PY'
import json
import sys

raw = sys.argv[1]
if not raw:
    raise SystemExit(1)
try:
    obj = json.loads(raw)
except Exception:
    raise SystemExit(1)
if obj.get("status") != "healthy":
    raise SystemExit(1)
PY
  then
    record_result "GREEN" "local_api_health" "reachable: $local_health_url"
  else
    record_result "YELLOW" "local_api_health" "not reachable at $local_health_url (start API if needed)"
  fi
fi

print_line() {
  local level="$1"
  local check="$2"
  local detail="$3"
  local color="$COLOR_RESET"
  case "$level" in
    RED) color="$COLOR_RED" ;;
    YELLOW) color="$COLOR_YELLOW" ;;
    GREEN) color="$COLOR_GREEN" ;;
  esac
  printf '%b%-6s%b %-30s %s\n' "$color" "$level" "$COLOR_RESET" "$check" "$detail"
}

printf 'Integration Preflight (%s)\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'Env source: %s\n\n' "$ENV_FILE"

for line in "${RESULT_LINES[@]}"; do
  IFS='|' read -r level check detail <<<"$line"
  print_line "$level" "$check" "$detail"
done

printf '\nSummary: GREEN=%d YELLOW=%d RED=%d\n' "$GREEN_COUNT" "$YELLOW_COUNT" "$RED_COUNT"

OVERALL="GREEN"
EXIT_CODE=0
if [[ "$RED_COUNT" -gt 0 ]]; then
  OVERALL="RED"
  EXIT_CODE=2
elif [[ "$YELLOW_COUNT" -gt 0 ]]; then
  OVERALL="YELLOW"
  EXIT_CODE=1
fi

case "$OVERALL" in
  GREEN)
    printf '%bOVERALL READINESS: %s%b\n' "$COLOR_GREEN" "$OVERALL" "$COLOR_RESET"
    ;;
  YELLOW)
    printf '%bOVERALL READINESS: %s%b\n' "$COLOR_YELLOW" "$OVERALL" "$COLOR_RESET"
    ;;
  RED)
    printf '%bOVERALL READINESS: %s%b\n' "$COLOR_RED" "$OVERALL" "$COLOR_RESET"
    ;;
esac

exit "$EXIT_CODE"
