# HederaShield Integration Harness Runbook

## Quick Start

```bash
cp .env.testnet.example .env.testnet
./scripts/run-integration-harness.sh --mode mock --env-file .env.testnet
```

Default mode is `mock` (safe/offline-style checks). Artifacts are generated under `artifacts/integration/<timestamp>/`.

## Modes

### 1) Mock/Demo Mode (default, credentials-optional)

```bash
./scripts/run-integration-harness.sh --mode mock --env-file .env.testnet
```

What it does:
- Runs env validation (`scripts/validate-testnet-env.py`)
- Runs smoke checks with Mirror Node network probe disabled
- Generates evidence artifacts (`report.md`, `report.json`, logs)

Use this mode for judge/demo environments with placeholder or missing private keys.

### 2) Real Testnet Mode (explicit opt-in)

```bash
HEDERA_SHIELD_ENABLE_REAL_TESTNET=1 \
./scripts/run-integration-harness.sh --mode real --env-file .env.testnet
```

Real mode requirements:
- `HEDERA_SHIELD_ENABLE_REAL_TESTNET=1` must be set
- `.env.testnet` must include non-placeholder operator id/key
- `HEDERA_SHIELD_HEDERA_NETWORK=testnet`

What it does:
- Runs env validation
- Runs live Mirror Node smoke probe
- Runs live read-only integration tests: `tests/test_integration_testnet.py`

Notes:
- Harness is designed for read-only validation; it does not run HTS enforcement transactions.
- To skip live pytest in real mode: `--skip-integration-tests`

## Artifact Output (Submission Evidence)

By default artifacts are written to:

```text
artifacts/integration/<UTC timestamp>/
```

Override location:

```bash
./scripts/run-integration-harness.sh \
  --mode mock \
  --env-file .env.testnet \
  --artifacts-dir artifacts/submission/mock
```

Generated files:
- `harness.log` (structured `HARNESS|...` lines)
- `validator.log`
- `smoke.log`
- `integration.log` (empty/skipped in mock mode)
- `report.md` (copy-paste friendly snippets)
- `report.json` (machine-readable status summary)

## Optional: Run API Demo After Harness

```bash
cp .env.testnet .env
python -m hedera_shield.api
curl -s http://localhost:8000/health
```

## Troubleshooting

- `real_opt_in` fail: set `HEDERA_SHIELD_ENABLE_REAL_TESTNET=1`.
- `real_creds` fail: replace placeholder operator credentials in `.env.testnet`.
- `smoke` fail in real mode: inspect `smoke.log`; mirror endpoint may be unavailable.
