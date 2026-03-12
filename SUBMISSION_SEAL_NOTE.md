# HederaShield Submission Seal Note

Seal timestamp (UTC): `2026-03-12T10:27:50Z`  
Status: **SUBMISSION-READY (SEALED)**

## Seal Statement

This package is sealed as submission-ready for manual portal submit.  
Scope is docs-only and no feature/code changes are included in this seal pass.

## Locked Core Docs

- [SUBMIT_OWNER_QUICK_CARD.md](SUBMIT_OWNER_QUICK_CARD.md)
- [OPERATOR_SIGNOFF_BRIEF.md](OPERATOR_SIGNOFF_BRIEF.md)
- [EXEC_HANDOFF_DIGEST.md](EXEC_HANDOFF_DIGEST.md)
- [READY_TO_SUBMIT_STATUS.md](READY_TO_SUBMIT_STATUS.md)
- [PORTAL_DRY_RUN_TRANSCRIPT.md](PORTAL_DRY_RUN_TRANSCRIPT.md)
- [SUBMIT_CONTROL_SHEET.md](SUBMIT_CONTROL_SHEET.md)
- [RELEASE_READINESS.md](RELEASE_READINESS.md)
- [SUBMISSION.md](SUBMISSION.md)
- [docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json](docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json)
- [docs/evidence/submit-now/SUBMIT_NOW_INDEX.md](docs/evidence/submit-now/SUBMIT_NOW_INDEX.md)
- [docs/evidence/submit-now/SUBMISSION_COMMANDS.md](docs/evidence/submit-now/SUBMISSION_COMMANDS.md)

## Manual Submit Owner Actions (Exact)

1. Run final gate checks from repo root:
   ```bash
   ./scripts/submission-readiness.sh
   ./scripts/pre_submit_guard.sh
   ./scripts/print_submit_now.sh
   ```
2. Capture submit-time SHA exactly: `git rev-parse HEAD`.
3. Open `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`.
4. Paste portal fields exactly from the packet (no wording edits).
5. Replace placeholders before clicking submit:
   - `TODO_ADD_DEMO_VIDEO_URL`
   - `TODO_ADD_FINAL_DEPLOYED_URL_OR_NA`
6. Verify portal `Commit SHA` equals local `git rev-parse HEAD`.
7. Click submit once.
8. Capture confirmation screenshot and UTC submit timestamp in sprint evidence.

## Cross-Links

- [SUBMIT_OWNER_QUICK_CARD.md](SUBMIT_OWNER_QUICK_CARD.md)
- [OPERATOR_SIGNOFF_BRIEF.md](OPERATOR_SIGNOFF_BRIEF.md)
- [EXEC_HANDOFF_DIGEST.md](EXEC_HANDOFF_DIGEST.md)
- [READY_TO_SUBMIT_STATUS.md](READY_TO_SUBMIT_STATUS.md)
- [PORTAL_DRY_RUN_TRANSCRIPT.md](PORTAL_DRY_RUN_TRANSCRIPT.md)
