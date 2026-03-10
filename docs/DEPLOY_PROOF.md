# HederaShield Deployment Proof Checklist

Use this checklist to assemble final deployment/testnet proof for submission.

## Required Evidence

- [ ] Harness run metadata
  - Mode used (`mock` or `real`)
  - UTC timestamp of run
  - Artifact directory path (`artifacts/integration/<timestamp>/`)
- [ ] Harness summary output
  - `HARNESS|summary|PASS|harness checks passed`
- [ ] Environment validation output
  - `HARNESS|validator|PASS|env file format accepted`
- [ ] Smoke check output
  - `HARNESS|smoke|PASS|smoke checks passed`
- [ ] Evidence report files
  - `report.md`
  - `report.json`
  - `harness.log`
  - `validator.log`
  - `smoke.log`
  - `integration.log`
- [ ] API health proof
  - `GET /health` response payload
- [ ] Transaction query proof
  - One `GET /transactions` response payload
- [ ] Hedera explorer transaction links (replace placeholders)
  - Mirror Node tx URL: `<https://testnet.mirrornode.hedera.com/api/v1/transactions/<TX_ID>>`
  - HashScan tx URL: `<https://hashscan.io/testnet/transaction/<TX_ID>>`

## Transaction Link Placeholders

Replace each placeholder with real transaction IDs from your run:

- `TX_ENFORCEMENT_OR_ALERT_1`: `<https://hashscan.io/testnet/transaction/TX_ENFORCEMENT_OR_ALERT_1>`
- `TX_ENFORCEMENT_OR_ALERT_2`: `<https://hashscan.io/testnet/transaction/TX_ENFORCEMENT_OR_ALERT_2>`
- `TX_HCS_AUDIT_MESSAGE`: `<https://hashscan.io/testnet/transaction/TX_HCS_AUDIT_MESSAGE>`

## Command Output Template

Copy and fill this section in your submission notes.

```text
# 1) Run integration harness
$ ./scripts/run-integration-harness.sh --mode mock --env-file .env.testnet
HARNESS|mode|PASS|running mode=mock
HARNESS|artifacts|PASS|writing artifacts to artifacts/integration/<timestamp>
HARNESS|validator|PASS|env file format accepted
HARNESS|smoke|PASS|smoke checks passed
HARNESS|integration_pytest|SKIP|mock mode skips live integration pytest
HARNESS|report|PASS|generated artifacts/integration/<timestamp>/report.md and report.json
HARNESS|summary|PASS|harness checks passed

# 2) Health endpoint proof
$ curl -s http://localhost:8000/health
{"status":"ok","network":"testnet","dry_run":true}

# 3) Transaction query proof
$ curl -s "http://localhost:8000/transactions?limit=1"
{"transactions":[...],"count":1}

# 4) Optional real-mode proof
$ HEDERA_SHIELD_ENABLE_REAL_TESTNET=1 ./scripts/run-integration-harness.sh --mode real --env-file .env.testnet
HARNESS|summary|PASS|harness checks passed
```

## Packaging Reference

After collecting artifacts, create submission bundle:

```bash
./scripts/package-submission.sh
```

Expected output archive:

```text
dist/submission-bundle.zip
```
