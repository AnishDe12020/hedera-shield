# HederaShield Submit-Now Evidence Index

Timestamp UTC: `2026-03-12T06:45:14Z`
Validated HEAD: `2b9a2b63b95dd54647bea1a91e1bb7f8bd1e6607`

## Exact Artifact Files and Proof Purpose

- `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`
  - Proves final portal field values are pre-filled and ready for manual submit copy/paste.
- `dist/portal-submission/portal-submission-packet-latest.md`
  - Proves human-readable portal packet was generated from current repository state.
- `dist/portal-submission/portal-submission-packet-latest.json`
  - Proves machine-readable packet metadata and references were generated for the same state.
- `dist/portal-submission/portal-submission-verify-latest.txt`
  - Proves packet reference verification passed (`PORTAL_VERIFY|summary|PASS`).
- `dist/submission-readiness-latest.txt`
  - Proves readiness gate passed (`READINESS|summary|PASS`).
- `dist/pre-submit-verify-latest.txt`
  - Proves pre-submit verification passed (`VERIFY|summary|PASS`).
- `dist/submission-freeze/submission-freeze-latest.md`
  - Proves immutable freeze manifest was captured for current commit + artifact set.
- `dist/submission-freeze/submission-freeze-latest.json`
  - Proves machine-verifiable freeze metadata (branch, commit SHA, checksums) for submit-time audit.
- `dist/submission-freeze/drift-verify-latest.md`
  - Proves drift verification report is available for operator review.
- `dist/submission-freeze/drift-verify-latest.json`
  - Proves drift verification passed with no checksum/commit drift (`DRIFT|summary|PASS`).
- `docs/evidence/submission-freeze/validation-snapshot-latest.md`
  - Proves full guard/readiness/packet/freeze verification chain passed in one freeze pass.
- `docs/evidence/submission-freeze/readiness-snapshot-latest.md`
  - Proves readiness + pre-submit summary counts at freeze time.
- `docs/evidence/submission-freeze/portal-packet-snapshot-latest.md`
  - Proves portal packet generation/verification status and checksums at freeze time.
- `docs/evidence/submission-freeze/submission-freeze-latest.md`
  - Proves frozen artifact hash table is mirrored into evidence docs.
- `docs/evidence/submission-freeze/submission-freeze-latest.json`
  - Proves frozen machine-readable manifest is mirrored into evidence docs.
- `docs/evidence/submission-freeze/drift-verify-latest.md`
  - Proves latest drift summary is mirrored into evidence docs.
- `docs/evidence/submission-freeze/drift-verify-latest.json`
  - Proves latest drift verification JSON is mirrored into evidence docs.
