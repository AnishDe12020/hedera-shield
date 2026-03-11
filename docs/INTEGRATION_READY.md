# Integration Ready Runbook (First Live Testnet Pass)

This runbook is for the first live testnet integration pass with HederaShield. It validates configuration and live read paths without requiring destructive on-chain actions.

## 1) Setup

```bash
cd /home/anish/hedera-shield
cp .env.testnet.example .env.testnet
# Edit .env.testnet with your real values where available.
```

Run preflight checks (traffic-light readiness):

```bash
./scripts/integration_preflight.sh --env-file .env.testnet
```

Interpretation:
- `OVERALL READINESS: GREEN` means ready to proceed.
- `OVERALL READINESS: YELLOW` means proceed with cautions noted (for example placeholder credentials or API not running yet).
- `OVERALL READINESS: RED` means blocked; fix the listed red checks first.

## 2) Validate Testnet Env Format

```bash
python3 scripts/validate-testnet-env.py .env.testnet
```

Expected output:
- `Validation passed: env format is compatible with offline testnet setup.`

## 3) Live Mirror Node Reachability + Integration Read Path

Smoke probe against mirror node:

```bash
./scripts/run-testnet-smoke.sh .env.testnet
```

Expected output includes:
- `SMOKE|mirror_probe|PASS|...`
- `SMOKE|summary|PASS|all checks passed`

Run read-only integration tests against testnet mirror node:

```bash
HEDERA_SHIELD_RUN_INTEGRATION=1 pytest -q tests/test_integration_testnet.py
```

Expected output:
- All tests in `tests/test_integration_testnet.py` pass.

## 4) Sample Event Ingestion (Live Read Through API)

Start API in one terminal:

```bash
set -a
source .env.testnet
set +a
python -m hedera_shield.api
```

In a second terminal, fetch live transactions (this is the ingestion/read verification step):

```bash
curl -s "http://127.0.0.1:${HEDERA_SHIELD_API_PORT:-8000}/transactions?limit=5" | python3 -m json.tool
```

Expected output characteristics:
- JSON object with keys `token_id`, `count`, and `transactions`.
- `count` is an integer.
- `transactions` is an array (may be empty if no recent events for configured token).

Also verify service health and status:

```bash
curl -s "http://127.0.0.1:${HEDERA_SHIELD_API_PORT:-8000}/health"
curl -s "http://127.0.0.1:${HEDERA_SHIELD_API_PORT:-8000}/status" | python3 -m json.tool
```

Expected output:
- Health: `{"status":"healthy"}`
- Status contains `status`, `monitored_tokens`, `total_alerts`, and `uptime_seconds`.

## 5) Capture Evidence Artifact

```bash
./scripts/run-live-integration.sh --env-file .env.testnet
```

Expected output:
- A line like `LIVE|evidence|PASS|docs/evidence/live-integration-<timestamp>.md`
- Evidence markdown created under `docs/evidence/`

## 6) Rollback / Cleanup

Stop API process:

```bash
# If running in foreground, use Ctrl+C
# If needed, terminate by process match:
pkill -f "python -m hedera_shield.api" || true
```

Remove runtime caches/artifacts from local run only (optional):

```bash
rm -rf .pytest_cache .ruff_cache
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
```

Do not commit secrets:

```bash
git status --short
# Ensure .env.testnet is not staged if it contains credentials.
```
