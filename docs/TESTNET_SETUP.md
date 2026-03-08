# HederaShield Testnet Setup and Smoke Runbook

## 1. Prepare Environment

```bash
cp .env.testnet.example .env.testnet
```

Populate `.env.testnet` with your values:

- `HEDERA_SHIELD_HEDERA_NETWORK=testnet`
- `HEDERA_SHIELD_HEDERA_OPERATOR_ID=0.0.x`
- `HEDERA_SHIELD_HEDERA_OPERATOR_KEY=<ed25519 private key>`
- `HEDERA_SHIELD_MIRROR_NODE_URL=https://testnet.mirrornode.hedera.com`
- `HEDERA_SHIELD_MONITORED_TOKEN_IDS=["0.0.x"]`

Validate format offline:

```bash
python3 scripts/validate-testnet-env.py .env.testnet
```

Expected success line:

```text
Validation passed: env format is compatible with offline testnet setup.
```

## 2. Run Testnet Smoke

```bash
./scripts/run-testnet-smoke.sh .env.testnet
```

Smoke output uses a stable machine-readable format:

```text
SMOKE|<check_name>|PASS|<details>
SMOKE|<check_name>|FAIL|<details>
```

Expected successful summary:

```text
SMOKE|summary|PASS|all checks passed
```

If you only want local/offline checks:

```bash
HEDERA_SHIELD_SMOKE_SKIP_NETWORK=1 ./scripts/run-testnet-smoke.sh .env.testnet
```

## 3. Start HederaShield with Testnet Config

```bash
cp .env.testnet .env
python -m hedera_shield.api
```

Health check:

```bash
curl -s http://localhost:8000/health
```

## 4. Optional Live Integration Tests

```bash
HEDERA_SHIELD_RUN_INTEGRATION=1 pytest -q tests/test_integration_testnet.py
```

## 5. Evidence Checklist

Collect the following artifacts for submission/review:

- `.env.testnet` validation output (`validate-testnet-env.py`)
- Smoke script output showing `SMOKE|summary|PASS|all checks passed`
- `/health` response from local API
- Sample `/transactions` response for a monitored token
- If enforcement is demonstrated: dry-run enforcement response payload
- If integration tests are run: `pytest` output for `tests/test_integration_testnet.py`
