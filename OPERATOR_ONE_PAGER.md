# HederaShield Operator One-Pager

## Purpose

Compact final operator flow for manual portal submission.

## Prerequisites

1. Run from repo root: `pwd` ends with `hedera-shield`.
2. Working tree clean enough for submit docs handoff: `git status --short`.
3. Final links ready to replace placeholders:
   - Demo URL (`TODO_ADD_DEMO_VIDEO_URL`)
   - Deployed URL or `N/A` (`TODO_ADD_FINAL_DEPLOYED_URL_OR_NA`)
4. Use packet source of truth:
   - `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`

## Exact Submit Order

1. `./scripts/submission-readiness.sh`
2. `./scripts/pre_submit_guard.sh`
3. `./scripts/pre-submit-verify.py`
4. `./scripts/print_submit_now.sh`
5. `git rev-parse HEAD` and keep this SHA for the portal form.
6. Open and copy portal fields from `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`.
7. Replace both required placeholders with final values.
8. Submit in portal.
9. Capture confirmation screenshot + UTC timestamp.

## Rollback / Abort Conditions

Abort submit immediately if any condition is true:

1. Any check command above returns non-zero or non-PASS summary.
2. Either placeholder token remains in the values being submitted.
3. Pasted commit SHA does not match current `git rev-parse HEAD`.
4. Required packet file is missing or unreadable.

If aborted:

1. Do not click submit.
2. Fix issue, rerun checks in exact order, then restart this one-pager flow.

## Post-Submit Verification

1. Re-run `git rev-parse HEAD` and record it in the submit log.
2. Save portal confirmation screenshot path + UTC time in handoff notes.
3. Confirm references stay aligned:
   - [READY_TO_SUBMIT_STATUS.md](READY_TO_SUBMIT_STATUS.md)
   - [HANDOFF_STAMP.md](HANDOFF_STAMP.md)
   - [PORTAL_SUBMISSION_MANIFEST.md](PORTAL_SUBMISSION_MANIFEST.md)
