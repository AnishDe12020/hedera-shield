# HederaShield Final Portal Submission Dry-Run

Last updated (UTC): `2026-03-12T04:16:41Z`

## Goal

Rehearse the exact end-to-end portal submission flow before the final click, and verify every required file/output is present.

## Step 1: Preflight Gate

Run:

```bash
./scripts/pre_submit_guard.sh
./scripts/submission-readiness.sh
./scripts/pre-submit-verify.py
```

Expected checkpoints:
- `GUARD|PASS|pre-submit guard complete`
- `READINESS|summary|PASS|submission readiness checks passed`
- `VERIFY|summary|PASS|pre-submit verification checks passed`

## Step 2: Refresh Portal Packet + Freeze

Run:

```bash
./scripts/generate-portal-submission-packet.py
./scripts/verify-portal-submission-packet.py
./scripts/submission-freeze.py
./scripts/verify-submission-freeze.py
```

Expected checkpoints:
- `PORTAL_VERIFY|summary|PASS`
- `DRIFT|summary|PASS`
- `dist/submission-freeze/submission-freeze-latest.md` exists
- `dist/submission-freeze/submission-freeze-latest.json` exists

## Step 3: Final Operator Handoff Helper

Run:

```bash
./scripts/final_portal_handoff.sh
```

Expected checkpoints:
- `HANDOFF|summary|PASS|all required files/checks present`
- Script prints final operator action list for the portal form.

## Step 4: Portal Rehearsal (No Submit Yet)

1. Open `dist/portal-submission/portal-submission-packet-latest.md` (fallback: `HEDERA_PORTAL_SUBMISSION_PACKET.md`).
2. Open the Hedera portal form and paste every section into the matching field.
3. Validate links are public (repo, demo video, optional deploy URL).
4. Confirm commit SHA in the form equals:

```bash
git rev-parse HEAD
```

Expected checkpoint:
- Every required field can be populated with no placeholder gaps.

## Step 5: Final Submit Pass

Immediately before real submission, re-run:

```bash
./scripts/final_portal_handoff.sh
```

Then submit in portal and capture:
- Confirmation screenshot
- UTC submit timestamp
- Final commit SHA used in form
