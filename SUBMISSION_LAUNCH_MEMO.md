# HederaShield Submission Launch Memo

Launch memo timestamp (UTC): `2026-03-12T11:31:23Z`
Launch owner: Submit Owner
Scope: Final docs-only launch authorization pass.

## Launch Readiness Snapshot

- Quick validation: **PASS** (`./scripts/submission-readiness.sh` -> `READINESS|summary|PASS`; `./scripts/pre-submit-verify.py` -> `VERIFY|summary|PASS`)
- Pre-submit guard: **PASS** (`./scripts/pre_submit_guard.sh` -> `GUARD|PASS|pre-submit guard complete (demo-id=3min-offline)`)
- Submit-now checks: **PASS** (`./scripts/print_submit_now.sh` -> required paths `CHECK|PASS`)

Current recommendation: **LAUNCH WHEN HUMAN FINAL ACTIONS COMPLETE**.

## Final Human Actions (Required)

1. Open `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json` and copy portal field values exactly.
2. Replace all portal placeholders before final click:
   - `TODO_ADD_DEMO_VIDEO_URL`
   - `TODO_ADD_FINAL_DEPLOYED_URL_OR_NA`
3. Capture submit-time SHA with `git rev-parse HEAD` and ensure exact portal `Commit SHA` match.
4. Submit once in Hedera portal.
5. Capture confirmation screenshot and UTC submission timestamp immediately.
6. Record submitted SHA + timestamp in handoff evidence docs.

## Explicit Launch / No-Launch Criteria

Launch only if all conditions are true:

- `READINESS|summary|PASS` from `./scripts/submission-readiness.sh`
- `VERIFY|summary|PASS` from `./scripts/pre-submit-verify.py`
- `GUARD|PASS` from `./scripts/pre_submit_guard.sh`
- No `CHECK|FAIL` in `./scripts/print_submit_now.sh`
- No unresolved placeholders in portal payload
- Portal `Commit SHA` exactly equals local `git rev-parse HEAD`

No-launch (block submit) if any of the following occurs:

- Any command above returns `FAIL` or missing summary PASS marker
- Portal packet file missing/inaccessible
- Any placeholder remains unresolved
- SHA mismatch between portal and local HEAD
- Human submit owner cannot capture screenshot + UTC timestamp immediately after submit

## Control Cross-Links

- [SUBMISSION_READINESS_ATTESTATION.md](SUBMISSION_READINESS_ATTESTATION.md)
- [SUBMISSION_DECISION_MEMO.md](SUBMISSION_DECISION_MEMO.md)
- [SUBMISSION_GATE_REPORT.md](SUBMISSION_GATE_REPORT.md)
- [SUBMIT_OWNER_QUICK_CARD.md](SUBMIT_OWNER_QUICK_CARD.md)
