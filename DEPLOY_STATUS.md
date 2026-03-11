# Deploy Status

**Timestamp:** 2026-03-11 05:57:10 CET (+0100)  
**Branch:** `master`

## 1) Full Test Suite

Command:
```bash
pytest
```

Result:
- **Total collected:** 106
- **Passed:** 100
- **Skipped:** 6
- **Failed:** 0
- **Duration:** 2.19s

## 2) One-Command Live Integration Run

Command:
```bash
source venv/bin/activate && ./scripts/run-live-integration.sh --env-file .env.testnet.example
```

Result:
- `validate-testnet-env`: **PASS**
- `run-testnet-smoke`: **PASS**
- `tests/test_integration_testnet.py`: **6 passed**
- Evidence markdown: `docs/evidence/live-integration-20260310T085339Z.md`

## 3) Deploy Readiness

Current state: **Read-only live testnet validation is green and evidence is captured.**

Deploy blocker status:
- **Blocker remains for state-changing deploy checks** until real non-placeholder operator credentials are configured.
- Required values: `HEDERA_SHIELD_HEDERA_OPERATOR_ID` and `HEDERA_SHIELD_HEDERA_OPERATOR_KEY` in `.env.testnet`.

## 4) References

- One-command live runner: `scripts/run-live-integration.sh`
- Testnet runbook: `docs/TESTNET_SETUP.md`
- Latest evidence file: `docs/evidence/live-integration-20260310T085339Z.md`
