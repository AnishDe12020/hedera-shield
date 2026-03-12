# HederaShield Release Readiness

Last updated (UTC): `2026-03-12T05:40:37Z`

## 1) Submission Readiness Snapshot

- Scope lock: docs/scripts only, no feature changes.
- Current validation state:
  - Refreshed quick checks at `2026-03-12T05:40:37Z` via release-candidate lock pass.
  - `./scripts/submission-readiness.sh`: `PASS`
  - `./scripts/pre-submit-verify.py`: `PASS`
  - `./scripts/pre_submit_guard.sh`: `PASS`
  - `./scripts/submission-freeze.py`: `PASS`
  - `./scripts/verify-submission-freeze.py`: `PASS`
  - Last full lint/unit sweep from `2026-03-12T05:29:02Z`: `ruff check hedera_shield/ tests/` (`PASS`), `venv/bin/pytest tests/ -v --tb=short` (`102 passed, 6 skipped`)
- Readiness gate commands to run immediately before portal submission:
  - `./scripts/pre_submit_guard.sh`
  - `./scripts/submission-readiness.sh`
  - `./scripts/pre-submit-verify.py`
  - `./scripts/generate-portal-submission-packet.py`
  - `./scripts/verify-portal-submission-packet.py`
  - `./scripts/print_submit_now.sh`
  - `./scripts/submission-freeze.py`
  - `./scripts/verify-submission-freeze.py`
- Freeze/evidence bundle references:
  - `RELEASE_CANDIDATE_LOCK.md`
  - `SUBMISSION_FREEZE.md`
  - `docs/evidence/submit-now/SUBMIT_NOW_INDEX.md`
  - `docs/evidence/submission-freeze/validation-snapshot-latest.md`
  - `docs/evidence/submission-freeze/readiness-snapshot-latest.md`
  - `docs/evidence/submission-freeze/portal-packet-snapshot-latest.md`
  - `docs/evidence/submission-freeze/submission-freeze-latest.md`
  - `docs/evidence/submission-freeze/submission-freeze-latest.json`
- Pass criteria:
  - `dist/submission-readiness-latest.txt` contains `READINESS|summary|PASS`
  - `dist/pre-submit-verify-latest.txt` contains `VERIFY|summary|PASS`
  - `dist/portal-submission/portal-submission-verify-latest.txt` contains `PORTAL_VERIFY|summary|PASS`
  - `dist/submission-freeze/submission-freeze-latest.md` and `.json` exist and match `HEAD`

## 2) Manual Portal Submission Steps

1. Run all commands in section 1 and confirm all gates are green.
2. Run `./scripts/final_portal_handoff.sh` and confirm `HANDOFF|summary|PASS`.
3. Follow `SUBMISSION_DRY_RUN.md` rehearsal once end-to-end without submitting.
4. Run `./scripts/print_submit_now.sh` and verify all listed key paths resolve.
5. Open `docs/evidence/submit-now/SUBMIT_NOW_INDEX.md`, then copy final portal answers from `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json` (fallback reference: `HEDERA_PORTAL_SUBMISSION_PACKET.md`).
6. Confirm `RELEASE_CANDIDATE_LOCK.md`, `SUBMISSION_FREEZE.md`, and `docs/evidence/submission-freeze/*-latest.*` files reflect the current locked bundle.
7. Paste final links (repo, demo, optional deploy URL) and verify public accessibility.
8. Confirm portal commit SHA matches `git rev-parse HEAD`.
9. Submit in portal and capture submission confirmation screenshot + UTC timestamp.
10. Store confirmation evidence locally and update `docs/HUMAN_HANDOFF_PLAYBOOK.md` if needed.

## 3) Remaining Blockers

- Real on-chain enforcement and live testnet proof still require valid testnet operator credentials in `.env.testnet`.
- Public demo video URL must be final and publicly reachable at submit time.
- Network/DNS conditions can block push/sync from constrained environments; use offline handoff if needed.

## 4) Exact Operator Handoff Actions

1. Verify local state:
   - `git status --short`
   - `git rev-parse --short HEAD`
2. Run final guard/validation:
   - `./scripts/pre_submit_guard.sh`
   - `./scripts/submission-readiness.sh`
   - `./scripts/pre-submit-verify.py`
3. Regenerate portal packet and freeze manifests:
   - `./scripts/generate-portal-submission-packet.py`
   - `./scripts/verify-portal-submission-packet.py`
   - `./scripts/print_submit_now.sh`
   - `./scripts/submission-freeze.py`
   - `./scripts/verify-submission-freeze.py`
4. Attempt final push path:
   - `./scripts/sync-and-submit.sh --max-retries 3 --initial-backoff-seconds 2 --max-backoff-seconds 16`
   - If blocked: `./scripts/network-recovery-push-runner.sh --check-interval-seconds 30 --max-checks 20`
   - If still blocked: `./scripts/offline-handoff.sh`
5. Execute portal submit:
   - Fill from `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json` (fallback: `HEDERA_PORTAL_SUBMISSION_PACKET.md`)
   - Confirm SHA + links + required evidence fields
   - Submit and archive confirmation proof
