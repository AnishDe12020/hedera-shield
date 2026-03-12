# HederaShield Submission-Ready Snapshot

- Snapshot UTC: `2026-03-12T06:35:38Z`
- Latest commit at snapshot time: `d3cafb4f53a1f2288ca98565c0ea3f2e07e4234a`
- Scope: docs-only final submission pass

## Validation and Guard Checks

Executed on `2026-03-12T06:35:22Z`:

1. `./scripts/submission-readiness.sh` -> `READINESS|summary|PASS`
2. `./scripts/pre_submit_guard.sh` -> `GUARD|PASS|pre-submit guard complete (demo-id=3min-offline)`
3. `./scripts/pre-submit-verify.py` -> `VERIFY|summary|PASS`
4. `./scripts/verify-portal-submission-packet.py` -> `PORTAL_VERIFY|summary|PASS`
5. `./scripts/print_submit_now.sh` -> all key artifact checks `CHECK|PASS`

Latest generated check reports:

- `dist/submission-readiness-20260312T063522Z.txt`
- `dist/pre-submit-verify-20260312T063522Z.txt`
- `dist/portal-submission/portal-submission-verify-20260312T063522Z.txt`
- `dist/submission-readiness-latest.txt`
- `dist/pre-submit-verify-latest.txt`
- `dist/portal-submission/portal-submission-verify-latest.txt`

## Required Artifacts Status

- `dist/submission-bundle.zip`: PASS
- `dist/release-evidence-20260310T122842Z.tar.gz`: PASS
- `artifacts/demo/3min-offline/harness/report.md`: PASS
- `artifacts/demo/3min-offline/harness/report.json`: PASS
- `artifacts/demo/3min-offline/submission-bundle.zip.sha256`: PASS
- `artifacts/integration/release-20260310T122842Z/release-report.md`: PASS
- `artifacts/integration/release-20260310T122842Z/release-report.json`: PASS

## Linked Control Docs and Submit-Now Packet

- [PRE_SUBMIT_RECAP.md](PRE_SUBMIT_RECAP.md)
- [SUBMISSION_PACKET_VERIFIED.md](SUBMISSION_PACKET_VERIFIED.md)
- [RELEASE_CANDIDATE_LOCK.md](RELEASE_CANDIDATE_LOCK.md)
- [docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json](docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json)

## Final Manual Submission Actions

1. Open `docs/evidence/submit-now/SUBMIT_NOW_INDEX.md` and `docs/evidence/submit-now/SUBMISSION_COMMANDS.md`.
2. Copy portal fields from `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`.
3. Replace placeholders with final public links and the final pushed commit SHA.
4. Submit in the Hedera portal.
5. Capture confirmation screenshot and record UTC submission timestamp in sprint notes.
