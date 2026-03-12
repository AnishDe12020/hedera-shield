# HederaShield Release Candidate Lock

Lock pass timestamp (UTC): `20260312T054037Z`  
Locked commit SHA (validated base): `ff902182f8586e0715853132a716243924973563`  
Branch: `master`  
Scope: docs/scripts only, no feature changes

## Frozen Artifacts

| Artifact | SHA-256 |
| --- | --- |
| `dist/submission-readiness-latest.txt` | `d613b2c63949478ab316c6d08663f69821aa9e8b13d0736d7033a47fde3cdd08` |
| `dist/pre-submit-verify-latest.txt` | `c8bf73d2ed0be2fec31a555a747db3766785ab8a13bb3ff1dc29460adf454e2e` |
| `dist/submission-freeze/submission-freeze-latest.md` | `014ed45a35c268ecdfb0a2ab633446d63aa3dcb218e9f04529686bdfdebd7289` |
| `dist/submission-freeze/submission-freeze-latest.json` | `a028983b3f0dca627778cb7ca96f0024cd4c2d4dc08448113473f6278e537e45` |
| `dist/submission-freeze/drift-verify-latest.md` | `a4be0272bfbcfc14f1af2051167826236c78f997822d575e988580f1464d2051` |
| `dist/submission-freeze/drift-verify-latest.json` | `b574426c75cee96a2a2115c89cda510f0df027c2f0acd453d999fdd2b6c58fa5` |

## Frozen Evidence/Status Docs

- `RELEASE_READINESS.md`
- `SUBMISSION_FREEZE.md`
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
4. Copy portal answers from `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json` (fallback: `HEDERA_PORTAL_SUBMISSION_PACKET.md`).
5. Confirm `RELEASE_CANDIDATE_LOCK.md`, `RELEASE_READINESS.md`, and `SUBMISSION_FREEZE.md` match the latest evidence snapshots.
6. Confirm portal SHA entry exactly matches `git rev-parse HEAD`.
7. Submit in Hedera portal manually.
8. Capture confirmation screenshot + UTC timestamp and archive with sprint notes.
