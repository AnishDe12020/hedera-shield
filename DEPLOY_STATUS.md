# Deploy Status

**Timestamp:** 2026-03-10 08:21:24 CET (+0100)
**Branch:** `master`

## 1) Full Test Suite

Command:
```bash
source venv/bin/activate && pytest
```

Result:
- **Total collected:** 68
- **Passed:** 62
- **Skipped:** 6
- **Failed:** 0
- **Duration:** 0.32s

Notes:
- Skipped tests are the gated integration set in `tests/test_integration_testnet.py` when `HEDERA_SHIELD_RUN_INTEGRATION` is not enabled in the full-suite run.

## 2) Integration Preflight

Preflight commands executed:
```bash
./scripts/run-testnet-smoke.sh .env.testnet.example
source venv/bin/activate && HEDERA_SHIELD_RUN_INTEGRATION=1 pytest -q tests/test_integration_testnet.py -q
```

Preflight result:
- `run-testnet-smoke.sh`: **PASS** (env format + testnet mirror probe checks)
- `tests/test_integration_testnet.py`: **6 passed**

Credential availability check:
- `.env.testnet` file: **not present**
- Exported `HEDERA_SHIELD_OPERATOR_ID` / `HEDERA_SHIELD_OPERATOR_KEY`: **not present**

## 3) Deploy Readiness

Current state: **Code and read-only testnet integration checks are green.**

Deployment/integration blocker:
- **Missing operator credentials** for state-changing Hedera actions and production-like end-to-end deploy validation.
- Specifically missing: `HEDERA_SHIELD_OPERATOR_ID` and `HEDERA_SHIELD_OPERATOR_KEY` (typically in `.env.testnet` or exported env).

## 4) Exact Next Commands

When credentials are available:
```bash
cp .env.testnet.example .env.testnet
# edit .env.testnet and set real values for:
# - HEDERA_SHIELD_OPERATOR_ID
# - HEDERA_SHIELD_OPERATOR_KEY

python3 scripts/validate-testnet-env.py .env.testnet
./scripts/run-testnet-smoke.sh .env.testnet
source venv/bin/activate && HEDERA_SHIELD_RUN_INTEGRATION=1 pytest -q tests/test_integration_testnet.py
cp .env.testnet .env
source venv/bin/activate && python -m hedera_shield.main
```

Git publish commands:
```bash
git add DEPLOY_STATUS.md
git commit -m "Add deploy status with test counts and integration preflight"
git push origin master
```
