# HederaShield Release Candidate Lock

Lock pass timestamp (UTC): `20260312T060500Z`  
Locked commit SHA (validated base): `446c1c6f083193bc93460220d14726c91a4839f7`  
Branch: `master`  
Scope: docs/scripts only, no feature changes

## Frozen Artifacts

| Artifact | SHA-256 |
| --- | --- |
| `dist/submission-readiness-latest.txt` | `fd1b2c01979a81d92eaf8c81d0d0fe3b16a49943ee05ed94bfb32d7ed5102908` |
| `dist/pre-submit-verify-latest.txt` | `1a86a97165b0e73bb537a44410471a4a4e0677816b8ce30f81e4c7022551d71f` |
| `dist/submission-freeze/submission-freeze-latest.md` | `a6a22c483cfde43ed58fef5d7646b1c725cdb0f7a1ec7345eab1385f6c42dea2` |
| `dist/submission-freeze/submission-freeze-latest.json` | `768f03fe50eab70b5cac0c4b8aad88956ae31ebc8d0b14ccf42c84699082456d` |
| `dist/submission-freeze/drift-verify-latest.md` | `6bfa3f52b5fe24a976be90187ca5a1a3f9886ae3223b967c2dfbc19ab538ca26` |
| `dist/submission-freeze/drift-verify-latest.json` | `af2853994b9dc64e170d48ed4bbaa241caa43e401df32fdaebaabb50fdb9a4fb` |

## Frozen Evidence/Status Docs

- `RELEASE_READINESS.md`
- `EVIDENCE_HYGIENE.md`
- `OPS_HANDOFF_CHECKLIST.md`
- `SUBMISSION_FREEZE.md`
- `docs/evidence/submit-now/SUBMISSION_COMMANDS.md`
- `docs/evidence/submission-freeze/validation-snapshot-latest.md`
- `docs/evidence/submission-freeze/readiness-snapshot-latest.md`
- `docs/evidence/submission-freeze/submission-freeze-latest.md`
- `docs/evidence/submission-freeze/submission-freeze-latest.json`
- `docs/evidence/submission-freeze/drift-verify-latest.md`
- `docs/evidence/submission-freeze/drift-verify-latest.json`

## Exact Human-Only Final Submission Actions

1. Confirm target commit on the submission machine:
   - `git rev-parse HEAD`
   - `git rev-parse --short HEAD`
2. Run final gate chain exactly once immediately before submit:
   - `./scripts/pre_submit_guard.sh`
   - `./scripts/submission-readiness.sh`
   - `./scripts/pre-submit-verify.py`
   - `./scripts/generate-portal-submission-packet.py`
   - `./scripts/verify-portal-submission-packet.py`
   - `./scripts/print_submit_now.sh`
   - `./scripts/submission-freeze.py`
   - `./scripts/verify-submission-freeze.py`
3. Open `docs/evidence/submit-now/SUBMIT_NOW_INDEX.md`.
4. Open `OPS_HANDOFF_CHECKLIST.md` and `docs/evidence/submit-now/SUBMISSION_COMMANDS.md`.
5. Copy portal answers from `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json` (fallback: `HEDERA_PORTAL_SUBMISSION_PACKET.md`).
6. Confirm `RELEASE_CANDIDATE_LOCK.md`, `RELEASE_READINESS.md`, and `SUBMISSION_FREEZE.md` match the latest evidence snapshots.
7. Confirm portal SHA entry exactly matches `git rev-parse HEAD`.
8. Submit in Hedera portal manually.
9. Capture confirmation screenshot + UTC timestamp and archive with sprint notes.
