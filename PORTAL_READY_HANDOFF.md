# HederaShield Portal-Ready Handoff

Handoff timestamp (UTC): `2026-03-12T07:20:01Z`
Scope: final docs-only operator handoff before Hedera portal submission

## Control Doc Cross-Links

- [READY_TO_SUBMIT_STATUS.md](READY_TO_SUBMIT_STATUS.md)
- [RELEASE_PACKAGE_INDEX.md](RELEASE_PACKAGE_INDEX.md)
- [PORTAL_SUBMISSION_MANIFEST.md](PORTAL_SUBMISSION_MANIFEST.md)
- [SUBMISSION_READY_SNAPSHOT.md](SUBMISSION_READY_SNAPSHOT.md)
- [PRE_SUBMIT_RECAP.md](PRE_SUBMIT_RECAP.md)

## Exact Final Operator Sequence

Run in repo root, in this exact order, immediately before opening final portal submit:

```bash
./scripts/submission-readiness.sh
./scripts/pre_submit_guard.sh
./scripts/pre-submit-verify.py
./scripts/generate-portal-submission-packet.py
./scripts/verify-portal-submission-packet.py
./scripts/print_submit_now.sh
```

Expected terminal summaries:

- `READINESS|summary|PASS`
- `GUARD|PASS|pre-submit guard complete (demo-id=3min-offline)`
- `VERIFY|summary|PASS`
- `PORTAL_PACKET|latest|PASS`
- `PORTAL_VERIFY|summary|PASS`
- submit-now path checks return `CHECK|PASS`

## Required Files (must exist before portal submit)

Source-of-truth submission docs:

- `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`
- `docs/evidence/submit-now/SUBMIT_NOW_INDEX.md`
- `docs/evidence/submit-now/SUBMISSION_COMMANDS.md`
- `HEDERA_PORTAL_SUBMISSION_PACKET.md` (fallback human-readable packet)

Latest check outputs:

- `dist/submission-readiness-latest.txt`
- `dist/pre-submit-verify-latest.txt`
- `dist/portal-submission/portal-submission-packet-latest.md`
- `dist/portal-submission/portal-submission-packet-latest.json`
- `dist/portal-submission/portal-submission-verify-latest.txt`
- `dist/portal-submission/portal-submission-verify-latest.json`

Core evidence artifacts:

- `dist/submission-bundle.zip`
- `dist/release-evidence-20260310T122842Z.tar.gz`
- `artifacts/demo/3min-offline/harness/report.md`
- `artifacts/demo/3min-offline/harness/report.json`

## Final Sanity Checks Before Portal Submit

1. `git rev-parse HEAD` is the commit you intend to submit.
2. Portal field values are copied from `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`.
3. No required portal field still contains placeholder values.
4. `dist/pre-submit-verify-latest.txt` contains `VERIFY|summary|PASS`.
5. `dist/portal-submission/portal-submission-verify-latest.txt` contains `PORTAL_VERIFY|summary|PASS`.
6. Demo video URL and deployed URL fields are final public values (or `N/A` where allowed).
7. After submit, capture confirmation screenshot and UTC timestamp in sprint notes.
