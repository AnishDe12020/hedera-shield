# HederaShield Submission Freeze

Freeze timestamp (UTC): `20260312T045355Z`
Freeze manifest source: `dist/submission-freeze/submission-freeze-latest.json`
Freeze commit SHA (validated base): `db3254f0b85cb05f1fe120175b1665beaf69a992`
Branch: `master`

## Locked Artifact Versions

| Artifact | SHA-256 |
| --- | --- |
| `dist/submission-readiness-latest.txt` | `fc2d088e54f99e964edeb74faf0143057471df42cfa0a01bb15cf2f0aae80ede` |
| `dist/pre-submit-verify-latest.txt` | `cdfe9a1cf13ee617aabf93d1a3d65b7b151536ad73e07db16084cfdb46e5893f` |
| `dist/portal-submission/portal-submission-packet-latest.md` | `f76b80da95d7010dad248e83a37c7cc59876efa1e264f4b8cc485c391689e5f8` |
| `dist/portal-submission/portal-submission-packet-latest.json` | `0b40cf5344f9d1cf9d3bc6319eb710e58ebadb6a80a5c3e2c2bbde13cae7b9e3` |
| `dist/portal-submission/portal-submission-verify-latest.txt` | `b96ac409efb84128725d1ea802b9ec19afba74a64fc4a5e0335579fa7b636a20` |
| `dist/submission-freeze/submission-freeze-latest.md` | `bf5028e3465db2b871e536b2754933ba2d5727d0d5bfd50d6caf60aae339dbbb` |
| `dist/submission-freeze/submission-freeze-latest.json` | `56d659baac933b066368b7689c4c2911e89a8df838a802ef41c4eaf34f277bbe` |
| `dist/submission-freeze/drift-verify-latest.md` | `0bcb6c98a69ba42ec0393634f6ca82b1fa1538e9c318d9092343413eaf4e9b50` |
| `dist/submission-freeze/drift-verify-latest.json` | `9332b2b352a6bf9136b14b1cc053e8763e25e452c65eb527d96a6ba2941b2161` |

## Evidence Bundle

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
2. Open `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json` and copy/paste final portal answers.
3. Confirm portal commit SHA is exactly `git rev-parse HEAD` from the submission machine.
4. Submit in the Hedera portal manually.
5. Capture confirmation screenshot + UTC timestamp and store with sprint notes.
