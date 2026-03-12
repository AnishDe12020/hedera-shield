# HederaShield Demo Runbook (3-5 Minutes)

Purpose: deliver a deterministic, offline-safe hackathon demo that shows the full compliance loop from monitored events to HCS audit reporting.

## 0) Problem (0:00-0:30)

Narration:
- Token issuers on Hedera need real-time compliance controls.
- Manual review is slow, and off-chain logs are weak for regulator-facing evidence.
- HederaShield adds detection, response guidance, and immutable HCS audit trail reporting.

## 1) Setup (0:30-1:00)

Show these commands:

```bash
# Offline-safe simulation path
./scripts/run-e2e-simulation.py

# Readiness gate (freshly re-run)
./scripts/submission-readiness.sh
./scripts/pre-submit-verify.py
```

Point to:
- `dist/submission-readiness-latest.txt`
- `dist/pre-submit-verify-latest.txt`

## 2) Monitored Events (1:00-2:00)

Narration:
- HederaShield ingests Hedera activity from Mirror Node style event streams.
- Demo input includes HTS-style transfers and account/token activity patterns.

Show evidence:
- Input samples: `demo/sample_hts_events.json`, `demo/sample_alerts.json`
- Simulation outputs: `artifacts/demo/e2e-simulation/<timestamp>/report.md`, `report.json`

## 3) Compliance Findings (2:00-3:00)

Narration:
- Engine evaluates each event against configurable built-in rules.
- Findings include severity, triggered rules, and recommended enforcement actions.

Show evidence:
- `artifacts/demo/3min-offline/harness/report.md`
- `artifacts/demo/3min-offline/harness/report.json`

Call out examples:
- Large transfer / velocity / structuring detection.
- Action recommendations for freeze, wipe, or KYC revoke in configured flows.

## 4) HCS Reporting (3:00-4:00)

Narration:
- Alerts are serialized into immutable audit messages via HCS reporter path.
- In judge-safe mode this is dry-run evidence, preserving deterministic output.

Show evidence:
- HCS reporting path in architecture docs: `README.md` and `SUBMISSION.md`
- Harness logs: `artifacts/demo/3min-offline/harness/harness.log`

## 5) Impact Close (4:00-5:00)

Narration:
- HederaShield is Hedera-native compliance infrastructure, not generic chain analytics.
- It combines detection, enforcement readiness, and immutable auditability for institutions.
- Submission assets are reproducible and ready for portal upload.

Show final proof:
- `dist/submission-bundle.zip`
- `dist/release-evidence-*.tar.gz`

## Latest Quick Validation Snapshot

As of `2026-03-12T03:33:10Z` (UTC):
- `ruff check hedera_shield/ tests/` -> PASS
- `venv/bin/pytest tests/ -v --tb=short` -> `102 passed, 6 skipped`
- `./scripts/package-submission.sh` -> PASS (`dist/submission-bundle.zip`, 39 files)
- `./scripts/submission-readiness.sh` -> PASS
- `./scripts/pre-submit-verify.py` -> PASS
