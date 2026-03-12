# HederaShield Ops Handoff Checklist

Purpose: final manual operator sequence for portal submission with minimal drift risk.

## T-30m: Stabilize + Rebuild Evidence

1. Confirm working tree and commit:
   - `git status --short`
   - `git rev-parse HEAD`
2. Rebuild submission-critical artifacts:
   - `./scripts/release-evidence.sh`
3. Run quick validation + guard:
   - `./scripts/submission-readiness.sh`
   - `./scripts/pre_submit_guard.sh`
4. Refresh submit packet + freeze manifests:
   - `./scripts/pre-submit-verify.py`
   - `./scripts/generate-portal-submission-packet.py`
   - `./scripts/verify-portal-submission-packet.py`
   - `./scripts/submission-freeze.py`
   - `./scripts/verify-submission-freeze.py`

## T-10m: Final Human Review

1. Open and verify:
   - `docs/evidence/submit-now/SUBMIT_NOW_INDEX.md`
   - `docs/evidence/submit-now/SUBMISSION_COMMANDS.md`
   - `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`
2. Confirm pass markers in latest reports:
   - `READINESS|summary|PASS` in `dist/submission-readiness-latest.txt`
   - `VERIFY|summary|PASS` in `dist/pre-submit-verify-latest.txt`
   - `PORTAL_VERIFY|summary|PASS` in `dist/portal-submission/portal-submission-verify-latest.txt`
3. Confirm freeze alignment:
   - `RELEASE_CANDIDATE_LOCK.md`, `RELEASE_READINESS.md`, and `SUBMISSION_FREEZE.md` reference the same final state.

## Submit: Portal Entry

1. Open the Hedera portal form.
2. Paste values from `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`.
3. Verify repository URL, demo URL, and commit SHA match current `HEAD`.
4. Submit once.

## Post-Submit Verification (T+0 to T+10m)

1. Capture proof:
   - Screenshot confirmation page.
   - Record UTC submit timestamp.
2. Record outcome in project docs/logs:
   - Update `PUSH_STATUS.md` (or sprint status artifact) with confirmation details.
3. Run final notification:
   - `openclaw system event --text 'Done: HederaShield ops handoff polish complete and pushed' --mode now`
