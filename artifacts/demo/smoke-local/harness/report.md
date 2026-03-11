# HederaShield Integration Harness Evidence

- Generated (UTC): `2026-03-11T03:07:44+00:00`
- Mode: `mock`
- Env file: `/home/anish/hedera-shield/.env.testnet.example`

## Check Summary
- `validator`: `PASS` (exit `0`)
- `smoke`: `PASS` (exit `0`)
- `integration_pytest`: `SKIP`
- `harness`: `PASS` (exit `0`)

## Harness Log
- File: `/home/anish/hedera-shield/artifacts/demo/smoke-local/harness/harness.log`
```text
HARNESS|mode|PASS|running mode=mock
HARNESS|artifacts|PASS|writing artifacts to artifacts/demo/smoke-local/harness
HARNESS|env_file|PASS|found .env.testnet.example
HARNESS|validator|PASS|env file format accepted
HARNESS|smoke|PASS|smoke checks passed
HARNESS|integration_pytest|SKIP|mock mode skips live integration pytest
```

## Validator Log
- File: `/home/anish/hedera-shield/artifacts/demo/smoke-local/harness/validator.log`
```text
Validation passed: env format is compatible with offline testnet setup.
```

## Smoke Log
- File: `/home/anish/hedera-shield/artifacts/demo/smoke-local/harness/smoke.log`
```text
SMOKE|env_file|PASS|found .env.testnet.example
SMOKE|python3|PASS|python3 is available
SMOKE|curl|PASS|curl is available
SMOKE|env_validation|PASS|validator accepted .env.testnet.example
SMOKE|network|PASS|HEDERA_SHIELD_HEDERA_NETWORK=testnet
SMOKE|mirror_url|PASS|using https://testnet.mirrornode.hedera.com
SMOKE|mirror_probe|PASS|skipped network call
SMOKE|summary|PASS|all checks passed
```

## Integration Pytest Log
- File: `/home/anish/hedera-shield/artifacts/demo/smoke-local/harness/integration.log`
```text
(no output)
```

## Submission Snippet
Use these files in your submission package:
- `/home/anish/hedera-shield/artifacts/demo/smoke-local/harness/report.md`
- `/home/anish/hedera-shield/artifacts/demo/smoke-local/harness/report.json`
- `/home/anish/hedera-shield/artifacts/demo/smoke-local/harness/validator.log`
- `/home/anish/hedera-shield/artifacts/demo/smoke-local/harness/smoke.log`
- `/home/anish/hedera-shield/artifacts/demo/smoke-local/harness/integration.log`
- `/home/anish/hedera-shield/artifacts/demo/smoke-local/harness/harness.log`
