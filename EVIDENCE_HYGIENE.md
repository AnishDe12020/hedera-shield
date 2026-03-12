# HederaShield Evidence Hygiene

Last updated (UTC): `2026-03-12T06:05:00Z`
Validated HEAD: `446c1c6f083193bc93460220d14726c91a4839f7`
Scope: docs/scripts only, no feature changes.

## Freshness Checks Executed

Validation and guard:
- `./scripts/pre_submit_guard.sh` -> `GUARD|PASS`
- `./scripts/submission-readiness.sh` -> `READINESS|summary|PASS`
- `./scripts/pre-submit-verify.py` -> `VERIFY|summary|PASS`

Portal packet:
- `./scripts/generate-portal-submission-packet.py` -> latest packet refreshed
- `./scripts/verify-portal-submission-packet.py` -> `PORTAL_VERIFY|summary|PASS`

Freeze and drift verification:
- `./scripts/submission-freeze.py` -> `FREEZE|summary|PASS`
- `./scripts/verify-submission-freeze.py` -> `DRIFT|summary|PASS`

## Pointer Sync Actions

Synchronized latest evidence pointers to current outputs:
- `docs/evidence/submission-freeze/submission-freeze-latest.md`
- `docs/evidence/submission-freeze/submission-freeze-latest.json`
- `docs/evidence/submission-freeze/drift-verify-latest.md`
- `docs/evidence/submission-freeze/drift-verify-latest.json`
- `docs/evidence/submission-freeze/validation-snapshot-latest.md`
- `docs/evidence/submission-freeze/readiness-snapshot-latest.md`
- `docs/evidence/submission-freeze/portal-packet-snapshot-latest.md`

## Update Cadence

- `Every evidence-affecting run`:
  - Rerun readiness + pre-submit + portal verify + freeze + drift verify.
  - Refresh all `*-latest` docs under `docs/evidence/submission-freeze/`.
- `T-30m before portal submit`:
  - Run full chain and confirm `PASS` summaries in latest reports.
- `T-10m before portal submit`:
  - Re-run `pre_submit_guard`, `pre-submit-verify`, `submission-freeze`, `verify-submission-freeze`.
- `Immediately pre-submit`:
  - Verify `RELEASE_READINESS.md`, `RELEASE_CANDIDATE_LOCK.md`, and this file still match current `dist/*-latest` checksums and `HEAD`.

## Canonical References

- `RELEASE_READINESS.md`
- `RELEASE_CANDIDATE_LOCK.md`
- `SUBMISSION_FREEZE.md`
- `docs/evidence/submit-now/SUBMIT_NOW_INDEX.md`
