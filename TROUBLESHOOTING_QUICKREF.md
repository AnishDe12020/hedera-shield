# HederaShield Troubleshooting Quick Reference

Use this for common integration/runtime failures during submission packaging and portal readiness checks.

## 1) DNS / Git Remote Unreachable

Failure signature:
```text
ssh: Could not resolve hostname github.com: Temporary failure in name resolution
fatal: Could not read from remote repository.
```

Remediation:
```bash
./scripts/sync-and-submit.sh --max-retries 3 --initial-backoff-seconds 2 --max-backoff-seconds 16
./scripts/network-recovery-push-runner.sh --check-interval-seconds 30 --max-checks 20
```

## 2) Portal Packet Verification Fails (Missing Referenced Path)

Failure signature:
```text
PORTAL_VERIFY|path_<n>|FAIL|missing <path>
PORTAL_VERIFY|summary|FAIL|portal submission packet is not ready
```

Remediation:
```bash
./scripts/generate-portal-submission-packet.py
./scripts/verify-portal-submission-packet.py
./scripts/pre-submit-verify.py
```

## 3) Submission Readiness Fails

Failure signature:
```text
READINESS|<check_key>|FAIL|...
READINESS|summary|FAIL|submission readiness checks failed
```

Remediation:
```bash
./scripts/submission-readiness.sh
./scripts/pre-submit-verify.py
./scripts/package-submission.sh
```

## 4) Real Testnet Run Blocked by Opt-In Guard

Failure signature:
```text
HEDERA_SHIELD_ENABLE_REAL_TESTNET is not set to 1
```

Remediation:
```bash
HEDERA_SHIELD_ENABLE_REAL_TESTNET=1 \
./scripts/run-integration-harness.sh --mode real --env-file .env.testnet
```

## 5) Placeholder/Invalid Testnet Credentials

Failure signature:
```text
SMOKE|env_validation|FAIL|...
```

Remediation:
```bash
./scripts/validate-testnet-env.py --env-file .env.testnet
./scripts/testnet-preflight.sh --env-file .env.testnet
```

Then set real values in `.env.testnet`:
- `HEDERA_SHIELD_HEDERA_OPERATOR_ID`
- `HEDERA_SHIELD_HEDERA_OPERATOR_KEY`

## 6) Integration Tests Skipped Unexpectedly

Failure signature:
```text
tests/test_integration_testnet.py::... SKIPPED
```

Remediation:
```bash
HEDERA_SHIELD_RUN_INTEGRATION=1 venv/bin/pytest -q tests/test_integration_testnet.py
```

## 7) Mirror Node/Network Flakiness

Failure signature:
```text
HTTP 429 / timeout / temporary upstream failures during smoke/integration checks
```

Remediation:
```bash
./scripts/run-testnet-smoke.sh --env-file .env.testnet
./scripts/run-live-integration.sh --env-file .env.testnet
```

## 8) Freeze Manifest Drift Mismatch

Failure signature:
```text
DRIFT|summary|FAIL|... differences detected
```

Remediation:
```bash
./scripts/submission-freeze.py
./scripts/verify-submission-freeze.py
```

## 9) Missing Submission Bundle

Failure signature:
```text
PACKAGE|required_files|FAIL|...
```

Remediation:
```bash
./scripts/package-submission.sh
ls -lh dist/submission-bundle.zip
```
