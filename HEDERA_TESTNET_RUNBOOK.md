# HederaShield Testnet Integration Runbook (Credentials-Ready)

This runbook is for the first live Hedera testnet integration pass after operator credentials are issued. It is designed for operator handoff and does not require committing secrets.

## 1) Prerequisites

- Repo cloned and dependencies installed.
- `python3`, `pytest`, and `curl` available on PATH.
- Hedera testnet operator account ID + private key.
- Testnet HBAR funded in operator account.
- One testnet token ID to monitor (fungible token recommended for first pass).

## 2) Prepare Environment File

```bash
cd /home/anish/hedera-shield
cp .env.testnet.example .env.testnet
```

Edit `.env.testnet` and set these required values:

- `HEDERA_SHIELD_HEDERA_NETWORK=testnet`
- `HEDERA_SHIELD_HEDERA_OPERATOR_ID=0.0.<operator_account_id>`
- `HEDERA_SHIELD_HEDERA_OPERATOR_KEY=<operator_private_key>`
- `HEDERA_SHIELD_MIRROR_NODE_URL=https://testnet.mirrornode.hedera.com`
- `HEDERA_SHIELD_MIRROR_NODE_POLL_INTERVAL=10`
- `HEDERA_SHIELD_API_HOST=0.0.0.0`
- `HEDERA_SHIELD_API_PORT=8000`
- `HEDERA_SHIELD_MONITORED_TOKEN_IDS=["0.0.<token_id>"]`
- `HEDERA_SHIELD_SANCTIONED_ADDRESSES=["0.0.111111"]` (or your policy list)

Optional AI fields:

- `HEDERA_SHIELD_ANTHROPIC_API_KEY=...`
- `HEDERA_SHIELD_AI_MODEL=claude-sonnet-4-20250514`

## 3) Funding + Token Setup

1. Fund the operator account with testnet HBAR (enough for API probes/tests and optional token tx fees).
2. Create or reuse a testnet token and capture the token ID (`0.0.x`).
3. Ensure monitored accounts are associated with the token if transfers will be generated.
4. Update `HEDERA_SHIELD_MONITORED_TOKEN_IDS` with that token ID.

## 4) Preflight Gate (Must Pass Before Live Run)

Strict preflight (requires `OVERALL READINESS: GREEN`):

```bash
./scripts/testnet-preflight.sh --env-file .env.testnet --timeout-seconds 8
```

Expected success output includes:

- `OVERALL READINESS: GREEN`
- `PREFLIGHT|summary|PASS|integration preflight gate passed`

## 5) Run Live Integration Harness

```bash
HEDERA_SHIELD_ENABLE_REAL_TESTNET=1 \
./scripts/run-integration-harness.sh --mode real --env-file .env.testnet
```

Expected success output includes:

- `HARNESS|real_opt_in|PASS|...`
- `HARNESS|real_network|PASS|network is testnet`
- `HARNESS|real_creds|PASS|operator credentials look non-placeholder`
- `HARNESS|smoke|PASS|smoke checks passed`
- `HARNESS|integration_pytest|PASS|live integration tests passed`
- `HARNESS|summary|PASS|harness checks passed`

Expected artifacts:

- `artifacts/integration/<timestamp>/harness.log`
- `artifacts/integration/<timestamp>/smoke.log`
- `artifacts/integration/<timestamp>/validator.log`
- `artifacts/integration/<timestamp>/integration.log`
- `artifacts/integration/<timestamp>/report.md`
- `artifacts/integration/<timestamp>/report.json`

## 6) Evidence Capture

```bash
./scripts/capture-testnet-evidence.sh --env-file .env.testnet --output docs/TESTNET_EVIDENCE.md
```

Expected success output includes:

- `EVIDENCE|summary|PASS|...`

## 7) Common Failure Modes

- `OVERALL READINESS: RED`
  - Fix all `RED` checks from preflight before running harness.
- `HARNESS|real_opt_in|FAIL|...`
  - Export `HEDERA_SHIELD_ENABLE_REAL_TESTNET=1`.
- `HARNESS|real_creds|FAIL|replace placeholder operator id/key...`
  - Replace placeholder credentials in `.env.testnet`.
- `HARNESS|smoke|FAIL|...`
  - Mirror node unreachable or env malformed; inspect `smoke.log`.
- `HARNESS|integration_pytest|FAIL|...`
  - Integration tests failed; inspect `integration.log`.
- `local_api_health` is `YELLOW` in preflight
  - Start API only if you need local health to pass:
    - `set -a; source .env.testnet; set +a; python -m hedera_shield.api`

## 8) Security / Handoff Notes

- Never commit `.env.testnet` with real credentials.
- Keep credentials in environment or secure secret manager.
- For safe offline verification without credentials, use:
  - `./scripts/release-evidence.sh`
  - `./scripts/run-integration-harness.sh --mode mock --env-file .env.testnet`
