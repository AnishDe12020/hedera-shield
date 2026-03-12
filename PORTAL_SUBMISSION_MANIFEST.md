# HederaShield Portal Submission Manifest

Manifest timestamp (UTC): `2026-03-12T06:45:14Z`
Scope: final portal submission copy/paste map (docs-only)

## Source of Truth

- Primary packet (machine-readable): `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`
- Control recap: `PRE_SUBMIT_RECAP.md`
- Submission-ready snapshot: `SUBMISSION_READY_SNAPSHOT.md`
- Generated packet reference: `dist/portal-submission/portal-submission-packet-latest.json`

## Final Gate Status (latest pass)

- `./scripts/submission-readiness.sh` -> `READINESS|summary|PASS`
- `./scripts/pre_submit_guard.sh` -> `GUARD|PASS|pre-submit guard complete (demo-id=3min-offline)`
- `./scripts/pre-submit-verify.py` -> `VERIFY|summary|PASS`
- `./scripts/generate-portal-submission-packet.py` -> `PORTAL_PACKET|latest|PASS`
- `./scripts/verify-portal-submission-packet.py` -> `PORTAL_VERIFY|summary|PASS`
- `./scripts/print_submit_now.sh` -> all required `CHECK|PASS`

## Portal Field Mapping (exact values)

1. Project Title
`HederaShield: Hedera-Native AI Compliance Agent`

2. Short Description
`AI-assisted, Hedera-native compliance monitoring and enforcement for HTS tokens with immutable HCS audit evidence.`

3. Full Description
Paste exact value from:
- `fields.full_description` in `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`

4. Architecture
Paste exact value from:
- `fields.architecture` in `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`

5. Innovation / Differentiation
Paste exact value from:
- `fields.innovation` in `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`

6. Setup / Repro Instructions
Paste exact value from:
- `fields.setup` in `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`

7. Demo Walkthrough Steps
Paste exact value from:
- `fields.demo_steps` in `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`

8. Judging Highlights
Paste exact value from:
- `fields.judging_highlights` in `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`

9. Repository URL
`https://github.com/AnishDe12020/hedera-shield`

10. Commit SHA
`2b9a2b63b95dd54647bea1a91e1bb7f8bd1e6607`

11. Branch
`master`

12. Demo Video URL
`TODO_ADD_DEMO_VIDEO_URL`  <-- REQUIRED PLACEHOLDER (replace before submit)

13. Deployed URL
`TODO_ADD_FINAL_DEPLOYED_URL_OR_NA`  <-- REQUIRED PLACEHOLDER (replace with final public URL or `N/A`)

## Evidence Files / Links To Paste Or Keep Ready

- Demo report (markdown): `artifacts/demo/3min-offline/harness/report.md`
- Demo report (json): `artifacts/demo/3min-offline/harness/report.json`
- Submission bundle: `dist/submission-bundle.zip`
- Release evidence bundle: `dist/release-evidence-20260310T122842Z.tar.gz`
- Human-readable fallback packet: `HEDERA_PORTAL_SUBMISSION_PACKET.md`

## Final Manual Guardrail

Before clicking submit, confirm:
1. `git rev-parse HEAD` equals `2b9a2b63b95dd54647bea1a91e1bb7f8bd1e6607`.
2. `TODO_ADD_DEMO_VIDEO_URL` has been replaced.
3. `TODO_ADD_FINAL_DEPLOYED_URL_OR_NA` has been replaced.
4. Portal entries were copied from `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`.
