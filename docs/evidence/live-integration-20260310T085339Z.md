# Live Integration Evidence

- Timestamp (UTC): `20260310T085339Z`
- Env file: `.env.testnet.example`
- Overall: `PASS`

## Command Status
- `python3 scripts/validate-testnet-env.py .env.testnet.example`: `PASS` (exit 0)
- `./scripts/run-testnet-smoke.sh .env.testnet.example`: `PASS` (exit 0)
- `HEDERA_SHIELD_RUN_INTEGRATION=1 pytest -q tests/test_integration_testnet.py`: `PASS` (exit 0)
- Integration pytest summary: `6 passed in 0.79s`

## Validator Output
```text
Validation passed: env format is compatible with offline testnet setup.
```

## Smoke Output
```text
SMOKE|env_file|PASS|found .env.testnet.example
SMOKE|python3|PASS|python3 is available
SMOKE|curl|PASS|curl is available
SMOKE|env_validation|PASS|validator accepted .env.testnet.example
SMOKE|network|PASS|HEDERA_SHIELD_HEDERA_NETWORK=testnet
SMOKE|mirror_url|PASS|using https://testnet.mirrornode.hedera.com
SMOKE|mirror_probe|PASS|mirror node returned network supply payload
SMOKE|summary|PASS|all checks passed
```

## Integration Pytest Output
```text
......                                                                   [100%]
6 passed in 0.79s
```
