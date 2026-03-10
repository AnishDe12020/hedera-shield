#!/usr/bin/env bash
set -u -o pipefail

ENV_FILE=".env.testnet"
OUTPUT_FILE="docs/TESTNET_EVIDENCE.md"
LIMIT="3"
FORCE_DRY_RUN=0
TX_IDS=()

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/capture-testnet-evidence.sh [--env-file FILE] [--output FILE] [--limit N] [--tx-id TX_ID] [--dry-run]

Options:
  --env-file FILE   Env file path (default: .env.testnet)
  --output FILE     Evidence markdown path (default: docs/TESTNET_EVIDENCE.md)
  --limit N         Number of transactions to fetch from mirror node (default: 3)
  --tx-id TX_ID     Include a specific transaction ID (repeatable)
  --dry-run         Force dry-run mode (no network calls)
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      ENV_FILE="${2:-}"
      shift 2
      ;;
    --output)
      OUTPUT_FILE="${2:-}"
      shift 2
      ;;
    --limit)
      LIMIT="${2:-}"
      shift 2
      ;;
    --tx-id)
      TX_IDS+=("${2:-}")
      shift 2
      ;;
    --dry-run)
      FORCE_DRY_RUN=1
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

emit() {
  local check="$1"
  local status="$2"
  local details="$3"
  printf 'EVIDENCE|%s|%s|%s\n' "$check" "$status" "$details"
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

if [[ ! "$LIMIT" =~ ^[0-9]+$ ]] || [[ "$LIMIT" == "0" ]]; then
  echo "--limit must be a positive integer" >&2
  exit 2
fi

if [[ ! -f "$ENV_FILE" ]]; then
  emit "env_file" "FAIL" "missing file: $ENV_FILE"
  exit 1
fi

MIRROR_URL="$(read_env_value "HEDERA_SHIELD_MIRROR_NODE_URL" "$ENV_FILE")"
NETWORK="$(read_env_value "HEDERA_SHIELD_HEDERA_NETWORK" "$ENV_FILE")"
OPERATOR_ID="$(read_env_value "HEDERA_SHIELD_HEDERA_OPERATOR_ID" "$ENV_FILE")"
OPERATOR_KEY="$(read_env_value "HEDERA_SHIELD_HEDERA_OPERATOR_KEY" "$ENV_FILE")"

if [[ -z "$NETWORK" ]]; then
  NETWORK="testnet"
fi
if [[ -z "$MIRROR_URL" ]]; then
  MIRROR_URL="https://testnet.mirrornode.hedera.com"
fi

DRY_RUN=0
DRY_REASON=""
if [[ "$FORCE_DRY_RUN" == "1" ]]; then
  DRY_RUN=1
  DRY_REASON="forced via --dry-run"
elif [[ -z "$OPERATOR_ID" || -z "$OPERATOR_KEY" ]]; then
  DRY_RUN=1
  DRY_REASON="missing operator credentials"
elif is_placeholder_account "$OPERATOR_ID" || is_placeholder_key "$OPERATOR_KEY"; then
  DRY_RUN=1
  DRY_REASON="placeholder operator credentials"
fi

TMP_TXS="$(mktemp)"
cleanup() {
  rm -f "$TMP_TXS"
}
trap cleanup EXIT

for tx in "${TX_IDS[@]}"; do
  if [[ -n "$tx" ]]; then
    printf '%s\t%s\n' "$tx" "N/A (manual)" >> "$TMP_TXS"
  fi
done

if [[ "$DRY_RUN" == "0" ]]; then
  QUERY_URL="${MIRROR_URL%/}/api/v1/transactions?account.id=$OPERATOR_ID&limit=$LIMIT&order=desc"
  RESPONSE="$(curl --silent --show-error --fail --max-time 20 "$QUERY_URL" 2>&1)"
  CURL_EXIT=$?
  if [[ $CURL_EXIT -ne 0 ]]; then
    emit "mirror_query" "FAIL" "curl failed for $QUERY_URL: $RESPONSE"
    exit 1
  fi

  if ! python3 - "$RESPONSE" "$TMP_TXS" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

raw = sys.argv[1]
out = Path(sys.argv[2])

data = json.loads(raw)
rows: list[str] = []
for item in data.get("transactions", []):
    tx_id = str(item.get("transaction_id", "")).strip()
    tx_hash = str(item.get("transaction_hash", "")).strip()
    if tx_id:
        rows.append(f"{tx_id}\t{tx_hash or 'N/A'}")

existing = out.read_text(encoding="utf-8").splitlines() if out.exists() else []
combined = existing + rows
seen: set[str] = set()
final: list[str] = []
for line in combined:
    tx = line.split("\t", 1)[0]
    if tx and tx not in seen:
        seen.add(tx)
        final.append(line)
out.write_text("\n".join(final) + ("\n" if final else ""), encoding="utf-8")
PY
  then
    emit "mirror_query" "FAIL" "failed to parse mirror node response"
    exit 1
  fi
  emit "mirror_query" "PASS" "captured transactions from $QUERY_URL"
else
  emit "mode" "DRY_RUN" "$DRY_REASON"
fi

if [[ ! -s "$TMP_TXS" ]]; then
  printf 'TX_ID_PLACEHOLDER_1\tN/A\n' >> "$TMP_TXS"
  printf 'TX_ID_PLACEHOLDER_2\tN/A\n' >> "$TMP_TXS"
fi

GENERATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
OUTPUT_DIR="$(dirname "$OUTPUT_FILE")"
mkdir -p "$OUTPUT_DIR"

{
  echo "# HederaShield Testnet Evidence"
  echo
  echo "- Generated (UTC): \`$GENERATED_AT\`"
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "- Capture mode: \`DRY_RUN\`"
  else
    echo "- Capture mode: \`LIVE\`"
  fi
  echo "- Env file: \`$ENV_FILE\`"
  echo "- Network: \`$NETWORK\`"
  echo "- Mirror node: \`$MIRROR_URL\`"
  echo
  echo "## Captured Transactions"
  echo
  echo "| tx_id | tx_hash | mirror_link | hashscan_link |"
  echo "|---|---|---|---|"

  while IFS=$'\t' read -r tx_id tx_hash; do
    [[ -z "$tx_id" ]] && continue
    mirror_link="${MIRROR_URL%/}/api/v1/transactions/${tx_id}"
    hashscan_link="https://hashscan.io/${NETWORK}/transaction/${tx_id}"
    echo "| \`$tx_id\` | \`$tx_hash\` | <$mirror_link> | <$hashscan_link> |"
  done < "$TMP_TXS"

  echo
  echo "## Reproduction Commands"
  echo
  echo "\`\`\`bash"
  echo "cp .env.testnet.example .env.testnet"
  echo "HEDERA_SHIELD_ENABLE_REAL_TESTNET=1 ./scripts/run-integration-harness.sh --mode real --env-file $ENV_FILE"
  echo "./scripts/capture-testnet-evidence.sh --env-file $ENV_FILE --output $OUTPUT_FILE --limit $LIMIT"
  echo "\`\`\`"

  if [[ "$DRY_RUN" == "1" ]]; then
    echo
    echo "## Dry-Run Next Steps"
    echo
    echo "Credentials are missing or placeholders; this file was generated in safe dry-run mode."
    echo
    echo "Run these exact commands after adding real testnet operator credentials:"
    echo
    echo "\`\`\`bash"
    echo "cp .env.testnet.example $ENV_FILE"
    echo "# edit $ENV_FILE and set non-placeholder HEDERA_SHIELD_HEDERA_OPERATOR_ID / HEDERA_SHIELD_HEDERA_OPERATOR_KEY"
    echo "HEDERA_SHIELD_ENABLE_REAL_TESTNET=1 ./scripts/run-integration-harness.sh --mode real --env-file $ENV_FILE"
    echo "./scripts/capture-testnet-evidence.sh --env-file $ENV_FILE --output $OUTPUT_FILE --limit $LIMIT"
    echo "\`\`\`"
  fi
} > "$OUTPUT_FILE"

emit "evidence_file" "PASS" "wrote $OUTPUT_FILE"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "Dry-run commands to execute after credentials are ready:"
  echo "cp .env.testnet.example $ENV_FILE"
  echo "HEDERA_SHIELD_ENABLE_REAL_TESTNET=1 ./scripts/run-integration-harness.sh --mode real --env-file $ENV_FILE"
  echo "./scripts/capture-testnet-evidence.sh --env-file $ENV_FILE --output $OUTPUT_FILE --limit $LIMIT"
fi

exit 0
