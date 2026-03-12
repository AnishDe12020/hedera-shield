# HederaShield Submit Control Sheet

Control timestamp (UTC): `2026-03-12T08:15:21Z`
Branch: `master`

## Pre-Submit Checks

Run from repo root in this exact order:

1. `./scripts/submission-readiness.sh` (expect `READINESS|summary|PASS`)
2. `./scripts/pre_submit_guard.sh` (expect `GUARD|PASS`)
3. `./scripts/pre-submit-verify.py` (expect `VERIFY|summary|PASS`)
4. `./scripts/print_submit_now.sh` (expect all `CHECK|PASS`)

Required control references:

- [EXEC_HANDOFF_DIGEST.md](EXEC_HANDOFF_DIGEST.md)
- [RELEASE_FREEZE_NOTE.md](RELEASE_FREEZE_NOTE.md)
- [COMMAND_REFERENCE_CARD.md](COMMAND_REFERENCE_CARD.md)
- [SUBMISSION_TERMINAL_CHECKLIST.md](SUBMISSION_TERMINAL_CHECKLIST.md)
- [OPERATOR_ONE_PAGER.md](OPERATOR_ONE_PAGER.md)
- [READY_TO_SUBMIT_STATUS.md](READY_TO_SUBMIT_STATUS.md)
- [HANDOFF_STAMP.md](HANDOFF_STAMP.md)

## Live Submit Steps

1. Capture live SHA: `git rev-parse HEAD`.
2. Open `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`.
3. Paste values into Hedera portal exactly as provided.
4. Replace placeholders before submit:
   - `TODO_ADD_DEMO_VIDEO_URL`
   - `TODO_ADD_FINAL_DEPLOYED_URL_OR_NA`
5. Confirm portal SHA equals step 1 SHA.
6. Click submit in portal.
7. Capture confirmation screenshot and UTC timestamp immediately.

## Immediate Post-Submit Checks

1. Re-run `git rev-parse HEAD` and record it with the confirmation timestamp.
2. Confirm screenshot is stored with sprint evidence artifacts.
3. Update handoff log with:
   - submit UTC time
   - submitted commit SHA
   - portal confirmation evidence path
4. Re-open linked control docs and ensure no contradictory status text remains.

## Escalation Paths

Use the first matching path:

1. Pre-submit script failure: stop submit; fix root cause; rerun full pre-submit sequence.
2. Packet mismatch or placeholder still present: do not submit; regenerate packet and re-verify with operator docs.
3. SHA mismatch at portal: abort submit, refresh local branch state, re-run checks, retry from pre-submit step 1.
4. Portal/UI failure after click: capture error screenshot/time, notify sprint lead, preserve logs and evidence files unchanged.
5. Ambiguous submit state (unsure if portal accepted): do not resubmit blindly; verify submission status with portal history/support, then proceed with documented guidance.
