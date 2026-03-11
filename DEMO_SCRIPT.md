# HederaShield Demo Script (3-5 Minutes)

Use this narrated walkthrough for a tight hackathon demo that does not require live credentials.

## 0:00-0:30 Problem

Narration:
"Compliance teams need real-time monitoring for Hedera Token Service activity, but they also need auditability and fast response. HederaShield watches HTS transfers, scores risk with deterministic rules plus optional AI context, and creates immutable reporting via HCS."

On screen:
- `README.md` architecture section
- Briefly show `hedera_shield/compliance.py`, `hedera_shield/scanner.py`, `hedera_shield/hcs_reporter.py`

## 0:30-1:10 Architecture

Narration:
"The flow is Mirror Node ingestion into the scanner, compliance evaluation across rule packs, optional enforcement recommendation, and HCS reporting for immutable evidence. FastAPI exposes status and alerts for operator workflows."

On screen:
- Architecture diagram in `README.md`
- Highlight modules:
  - Scanner: mirror-node polling + normalization
  - Compliance engine: multi-rule findings and severities
  - HCS reporter: immutable publish path

## 1:10-2:10 Sample HTS Event Flow (Credential-Free)

Run:
```bash
./scripts/smoke.sh
```

Narration:
"This smoke run validates environment shape, then executes a mock integration harness. No private keys are required, and no state-changing operations run. It still proves pipeline readiness and artifact generation."

On screen:
- `SMOKE|...|PASS|...` lines
- `HARNESS|summary|PASS|harness checks passed`
- Generated artifacts in `artifacts/demo/smoke-local/`

## 2:10-3:20 Compliance Findings

Narration:
"HederaShield flags patterns like large transfers, velocity bursts, sanctioned counterparties, structuring, dormant reactivation, and wash-like behavior. Findings are severity-tagged and become reviewable evidence for analysts."

On screen:
- `demo/sample_alerts.json`
- `artifacts/demo/smoke-local/harness/report.md`
- Mention how findings map to configurable rules in `config/rules.yaml`

## 3:20-4:10 HCS Reporting

Narration:
"Every finalized alert is publishable to HCS, giving tamper-evident compliance history with timestamps and a schema version. That means audit teams can independently verify what was flagged and when."

On screen:
- `hedera_shield/hcs_reporter.py`
- `README.md` section: Immutable Audit Trail (HCS)
- Optional: note mirror-topic retrieval path shown in project docs

## 4:10-5:00 Submission Readiness Close

Narration:
"The project ships with a submission checklist, smoke verifier, and packaged evidence workflow. Judges can reproduce a deterministic, credential-free run and inspect artifacts directly."

On screen:
- `SUBMISSION_CHECKLIST.md`
- `./scripts/package-submission.sh`
- `dist/submission-bundle.zip` if present

## Demo Commands (copy/paste)

```bash
./scripts/smoke.sh
./scripts/package-submission.sh
```

Optional full validation:
```bash
ruff check hedera_shield/ tests/
pytest tests/ -v --tb=short
```
