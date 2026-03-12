# HederaShield Submission Closure Checklist

Checklist timestamp (UTC): `2026-03-12T14:47:10Z`  
Scope: Compact final manual submit closure checklist.

## Pre-Submit

- [ ] Run `./scripts/submission-readiness.sh` and confirm `READINESS|summary|PASS`.
- [ ] Run `./scripts/pre-submit-verify.py` and confirm `VERIFY|summary|PASS`.
- [ ] Run `./scripts/pre_submit_guard.sh` and confirm `GUARD|PASS|pre-submit guard complete`.
- [ ] Run `./scripts/generate-portal-submission-packet.py` and confirm latest packet outputs are refreshed.
- [ ] Run `./scripts/verify-portal-submission-packet.py` and confirm `PORTAL_VERIFY|summary|PASS`.
- [ ] Run `./scripts/print_submit_now.sh` and confirm all required paths are `CHECK|PASS`.
- [ ] Run `python3 scripts/generate-submit-now-packet.py` and confirm `SUBMIT_NOW|summary|PASS`.
- [ ] Open `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json` as the canonical portal value source.
- [ ] Replace any unresolved placeholders with final public links and exact `git rev-parse HEAD` SHA.

## Submit

- [ ] Enter portal fields from `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`.
- [ ] Verify final values one last time against packet/docs.
- [ ] Submit once in the Hedera portal.

## Post-Submit

- [ ] Capture portal confirmation screenshot.
- [ ] Record exact UTC submit timestamp.
- [ ] Update handoff/control docs with confirmation details.

## Cross-Links

- [SUBMISSION_CLOSURE_RECAP.md](SUBMISSION_CLOSURE_RECAP.md)
- [SUBMISSION_CLOSURE_NOTE.md](SUBMISSION_CLOSURE_NOTE.md)
- [FINALITY_CHECK.md](FINALITY_CHECK.md)
- [SUBMISSION_SIGNOFF_LEDGER.md](SUBMISSION_SIGNOFF_LEDGER.md)
- [SUBMISSION_READINESS_BOARD.md](SUBMISSION_READINESS_BOARD.md)
