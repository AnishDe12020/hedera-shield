# HederaShield 3-Minute Demo Narration Outline

Use this script while following `docs/DEMO_RECORDING_RUNBOOK.md`.

## Timestamped Narration

### 0:00-0:20 - Reset deterministic demo workspace
- Narration: "I am running the offline-safe flow so judges can reproduce this without network or credentials. I set `DEMO_ID=3min-offline`, reset the directory, and start from a clean artifact path."
- Show on screen: setup commands from the runbook and resulting `artifacts/demo/3min-offline/` path.

### 0:20-1:20 - Run mock integration harness
- Narration: "This harness validates environment format and runs smoke checks in mock mode. It produces machine-readable and human-readable reports."
- Show on screen: `HARNESS|mode|PASS|running mode=mock`, `HARNESS|validator|PASS`, `HARNESS|smoke|PASS`, `HARNESS|summary|PASS`.
- Point to outputs: `harness.log`, `validator.log`, `smoke.log`, `report.md`, `report.json` under `artifacts/demo/3min-offline/harness/`.

### 1:20-2:00 - Build the submission bundle
- Narration: "Now I package the required repository docs and scripts into `dist/submission-bundle.zip` so the judging package is reproducible."
- Show on screen: `PACKAGE|required_files|PASS` and `PACKAGE|bundle|PASS|created .../dist/submission-bundle.zip`.

### 2:00-2:20 - Record bundle checksum
- Narration: "I capture a SHA-256 digest for integrity verification."
- Show on screen: `sha256sum dist/submission-bundle.zip` output and saved file `artifacts/demo/3min-offline/submission-bundle.zip.sha256`.

### 2:20-2:40 - Run readiness and draft verifier
- Narration: "Before submission, I run readiness checks and a final draft-linked verifier that validates every required doc and artifact path."
- Show on screen: `./scripts/submission-readiness.sh` then `./scripts/pre-submit-verify.py`.
- Point to outputs: `dist/submission-readiness-latest.txt` and `dist/pre-submit-verify-latest.txt`.

### 2:40-3:00 - Close with evidence index
- Narration: "This evidence trail is the final handoff path referenced by the submission checklist and draft pack."
- Show on screen: sorted `find "$DEMO_DIR" -maxdepth 2 -type f | sort` output and `docs/FINAL_SUBMISSION_CHECKLIST.md`.

## Optional 20-second add-on if real testnet was enabled
- Narration: "If real mode is explicitly enabled, we run the same harness with `--mode real` and attach those artifacts separately in `artifacts/demo/3min-real/`."
