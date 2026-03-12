# HederaShield Submission Freeze

Freeze timestamp (UTC): `20260312T052902Z`
Freeze manifest source: `dist/submission-freeze/submission-freeze-latest.json`
Freeze commit SHA (validated base): `c0dd5024511c8c7e12a9283665c66f3b185276e2`
Branch: `master`

## Locked Artifact Versions

| Artifact | SHA-256 |
| --- | --- |
| `dist/submission-readiness-latest.txt` | `d5a78a00486e905d17b3f74f1609390759f8242be7e67005779270e1c9fc1d57` |
| `dist/pre-submit-verify-latest.txt` | `51eee1395ec5e99a3ef559154ce9e707bdbeb94ed8e05cb476445d0b90cf0987` |
| `dist/portal-submission/portal-submission-packet-latest.md` | `ddc3be0ff759a914a92f673116a70702d26d2b52b5299a220e643f4afeb6f3fa` |
| `dist/portal-submission/portal-submission-packet-latest.json` | `32f3ebcb064f66ae0522382721e69553ff2fc0284fa7745459ed29895c9b0abb` |
| `dist/portal-submission/portal-submission-verify-latest.txt` | `fc8ea2d8fbcf094eb29cf010ecb9b9675d9d42fff718680098c873d57bd10aeb` |
| `dist/submission-freeze/submission-freeze-latest.md` | `9ee3c3266ec7572ace7cdd6ab2e0667ac97f5d34067d8d780c95161ab4b84861` |
| `dist/submission-freeze/submission-freeze-latest.json` | `aa3241c97d45ec9001598ca098f649a3266566bc8bbedba16f5fcc99450caa9c` |
| `dist/submission-freeze/drift-verify-latest.md` | `190e3b5f28812b9130b657a61601563eb71ae9accaebe74f98cec6a0e5784ebd` |
| `dist/submission-freeze/drift-verify-latest.json` | `c0c2334ebdbefda0ab1c912ac1b2047b26c4b8ec93fc6e9ce64e3888cd86bb9d` |

## Evidence Bundle

- `docs/evidence/submit-now/SUBMIT_NOW_INDEX.md`
- `docs/evidence/submission-freeze/validation-snapshot-latest.md`
- `docs/evidence/submission-freeze/readiness-snapshot-latest.md`
- `docs/evidence/submission-freeze/portal-packet-snapshot-latest.md`
- `docs/evidence/submission-freeze/submission-freeze-latest.md`
- `docs/evidence/submission-freeze/submission-freeze-latest.json`
- `docs/evidence/submission-freeze/drift-verify-latest.md`
- `docs/evidence/submission-freeze/drift-verify-latest.json`

## Manual-Only Submission Steps

1. Run the final gate chain exactly once at submit time:
   - `./scripts/pre_submit_guard.sh`
   - `./scripts/submission-readiness.sh`
   - `./scripts/pre-submit-verify.py`
   - `./scripts/generate-portal-submission-packet.py`
   - `./scripts/verify-portal-submission-packet.py`
   - `./scripts/submission-freeze.py`
   - `./scripts/verify-submission-freeze.py`
2. Open `docs/evidence/submit-now/SUBMIT_NOW_INDEX.md` and then copy/paste final portal answers from `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`.
3. Confirm portal commit SHA is exactly `git rev-parse HEAD` from the submission machine.
4. Submit in the Hedera portal manually.
5. Capture confirmation screenshot + UTC timestamp and store with sprint notes.
