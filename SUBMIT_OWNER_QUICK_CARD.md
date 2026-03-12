# HederaShield Submit Owner Quick Card

Use this one-screen card for manual portal submit control.

## Before Submit

- Run quick validation: `./scripts/pre-submit-verify.py` and stop if `VERIFY|summary|PASS` is missing.
- Run pre-submit guard: `./scripts/pre_submit_guard.sh` and stop if `GUARD|PASS` is missing.
- Run submit-now checks: `./scripts/print_submit_now.sh` and stop if any `CHECK|FAIL` appears.
- Capture submit-time SHA: `git rev-parse HEAD`; stop if SHA cannot be copied exactly.
- Open packet: `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`; stop if unavailable.

## During Submit

- Paste portal fields exactly from packet; stop on any manual wording drift.
- Replace all placeholders before click:
  - `TODO_ADD_DEMO_VIDEO_URL`
  - `TODO_ADD_FINAL_DEPLOYED_URL_OR_NA`
- Verify portal `Commit SHA` equals local SHA; stop on mismatch.
- Click submit once only; stop if any field is uncertain and re-validate first.

## After Submit

- Capture confirmation screenshot immediately; stop if screenshot is missing.
- Record UTC submit timestamp and submitted SHA in sprint evidence; stop if either is missing.
- Link evidence into the active handoff thread/docs before signoff.

## Control Cross-Links

- [SUBMISSION_READINESS_ATTESTATION.md](SUBMISSION_READINESS_ATTESTATION.md)
- [SUBMISSION_DECISION_MEMO.md](SUBMISSION_DECISION_MEMO.md)
- [SUBMISSION_LAUNCH_MEMO.md](SUBMISSION_LAUNCH_MEMO.md)
- [SUBMISSION_CONFIDENCE_SUMMARY.md](SUBMISSION_CONFIDENCE_SUMMARY.md)
- [SUBMISSION_HANDOFF_MATRIX.md](SUBMISSION_HANDOFF_MATRIX.md)
- [SUBMISSION_SEAL_NOTE.md](SUBMISSION_SEAL_NOTE.md)
- [OPERATOR_SIGNOFF_BRIEF.md](OPERATOR_SIGNOFF_BRIEF.md)
- [READY_TO_SUBMIT_STATUS.md](READY_TO_SUBMIT_STATUS.md)
- [SUBMISSION_GATE_REPORT.md](SUBMISSION_GATE_REPORT.md)
- [PORTAL_DRY_RUN_TRANSCRIPT.md](PORTAL_DRY_RUN_TRANSCRIPT.md)
