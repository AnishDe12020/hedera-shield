# HederaShield Integration Harness Evidence

- Generated (UTC): `2026-03-10T12:28:44+00:00`
- Mode: `mock`
- Env file: `/home/anish/hedera-shield/.env.testnet.example`

## Check Summary
- `validator`: `PASS` (exit `0`)
- `smoke`: `PASS` (exit `0`)
- `integration_pytest`: `SKIP`
- `harness`: `PASS` (exit `0`)

## Harness Log
- File: `/home/anish/hedera-shield/artifacts/integration/release-20260310T122842Z/mock/harness.log`
```text
HARNESS|mode|PASS|running mode=mock
HARNESS|artifacts|PASS|writing artifacts to artifacts/integration/release-20260310T122842Z/mock
HARNESS|env_file|PASS|found .env.testnet.example
HARNESS|validator|PASS|env file format accepted
HARNESS|smoke|PASS|smoke checks passed
HARNESS|integration_pytest|SKIP|mock mode skips live integration pytest
```

## Validator Log
- File: `/home/anish/hedera-shield/artifacts/integration/release-20260310T122842Z/mock/validator.log`
```text
Validation passed: env format is compatible with offline testnet setup.
```

## Smoke Log
- File: `/home/anish/hedera-shield/artifacts/integration/release-20260310T122842Z/mock/smoke.log`
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
- File: `/home/anish/hedera-shield/artifacts/integration/release-20260310T122842Z/mock/integration.log`
```text
(no output)
```

## Submission Snippet
Use these files in your submission package:
- `/home/anish/hedera-shield/artifacts/integration/release-20260310T122842Z/mock/report.md`
- `/home/anish/hedera-shield/artifacts/integration/release-20260310T122842Z/mock/report.json`
- `/home/anish/hedera-shield/artifacts/integration/release-20260310T122842Z/mock/validator.log`
- `/home/anish/hedera-shield/artifacts/integration/release-20260310T122842Z/mock/smoke.log`
- `/home/anish/hedera-shield/artifacts/integration/release-20260310T122842Z/mock/integration.log`
- `/home/anish/hedera-shield/artifacts/integration/release-20260310T122842Z/mock/harness.log`
