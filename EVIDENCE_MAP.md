# HederaShield Evidence Map

Evidence map timestamp (UTC): `2026-03-12T08:45:00Z`
Scope: map judging and submission claims to exact repository evidence paths.

## Judging Claims -> Evidence Paths

| Claim ID | Claim | Exact evidence paths |
| --- | --- | --- |
| J1 | Problem clarity and relevance are documented for judge review. | `README.md`, `SUBMISSION.md`, `docs/SUBMISSION_FORM_DRAFT_PACK.md`, `HEDERA_PORTAL_SUBMISSION_PACKET.md` |
| J2 | Technical depth and implementation quality are demonstrated with code, tests, and release checks. | `README.md`, `hedera_shield/`, `tests/`, `scripts/release-evidence.sh`, `dist/submission-bundle.zip`, `artifacts/integration/release-20260310T122842Z/release-report.md`, `artifacts/integration/release-20260310T122842Z/release-report.json` |
| J3 | Hedera integration is explicit (HTS, Mirror Node, HCS, SDK, testnet flow). | `docs/TESTNET_SETUP.md`, `docs/TESTNET_EVIDENCE.md`, `docs/DEPLOY_PROOF.md`, `HEDERA_TESTNET_RUNBOOK.md`, `SUBMISSION.md` |
| J4 | AI/agent usage and operator controls are documented. | `HEDERA_PORTAL_SUBMISSION_PACKET.md`, `README.md`, `docs/SUBMISSION_FORM_DRAFT_PACK.md`, `scripts/submission-readiness.sh`, `scripts/pre-submit-verify.py` |
| J5 | Demo quality and reproducibility are backed by runbooks and artifacts. | `docs/DEMO_RECORDING_RUNBOOK.md`, `docs/DEMO_NARRATION_3MIN.md`, `artifacts/demo/3min-offline/harness/report.md`, `artifacts/demo/3min-offline/harness/report.json`, `artifacts/demo/3min-offline/harness/harness.log`, `artifacts/demo/3min-offline/harness/smoke.log`, `artifacts/demo/3min-offline/harness/validator.log` |
| J6 | Submission completeness and reviewer UX are validated by checklist + packet verification outputs. | `docs/FINAL_SUBMISSION_CHECKLIST.md`, `docs/SUBMISSION_FORM_DRAFT_PACK.md`, `dist/portal-submission/portal-submission-packet-latest.md`, `dist/portal-submission/portal-submission-verify-latest.txt`, `docs/KNOWN_ISSUES_AND_WORKAROUNDS.md` |
| J7 | Quick judge validation path is defined. | `docs/JUDGING_ALIGNMENT.md`, `HEDERA_PORTAL_SUBMISSION_PACKET.md`, `dist/portal-submission/portal-submission-verify-latest.txt` |

## Submission Claims -> Evidence Paths

| Claim ID | Submission claim | Exact evidence paths |
| --- | --- | --- |
| S1 | Project title and positioning: Hedera-native AI compliance agent. | `PORTAL_SUBMISSION_MANIFEST.md`, `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`, `HEDERA_PORTAL_SUBMISSION_PACKET.md` |
| S2 | Short description claim: AI-assisted Hedera-native monitoring + HCS audit evidence. | `PORTAL_SUBMISSION_MANIFEST.md`, `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`, `SUBMISSION.md` |
| S3 | Full description field is sourced from the submit-now packet JSON. | `PORTAL_SUBMISSION_MANIFEST.md`, `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`, `dist/portal-submission/portal-submission-packet-latest.json` |
| S4 | Architecture field is sourced from the submit-now packet JSON. | `PORTAL_SUBMISSION_MANIFEST.md`, `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`, `docs/SUBMISSION_FORM_DRAFT_PACK.md` |
| S5 | Innovation/differentiation field is sourced from the submit-now packet JSON. | `PORTAL_SUBMISSION_MANIFEST.md`, `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`, `docs/SUBMISSION_FORM_DRAFT_PACK.md` |
| S6 | Setup/repro field is sourced from the submit-now packet JSON and executable scripts. | `PORTAL_SUBMISSION_MANIFEST.md`, `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`, `scripts/pre_submit_guard.sh`, `scripts/submission-readiness.sh`, `scripts/pre-submit-verify.py` |
| S7 | Demo walkthrough field is sourced from the submit-now packet JSON and runbook docs. | `PORTAL_SUBMISSION_MANIFEST.md`, `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`, `docs/DEMO_RECORDING_RUNBOOK.md`, `docs/DEMO_NARRATION_3MIN.md` |
| S8 | Judging highlights field is sourced from the submit-now packet JSON and alignment doc. | `PORTAL_SUBMISSION_MANIFEST.md`, `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`, `docs/JUDGING_ALIGNMENT.md` |
| S9 | Repository URL and branch/commit submission values are defined with command source. | `PORTAL_SUBMISSION_MANIFEST.md`, `EXEC_HANDOFF_DIGEST.md`, `docs/evidence/submit-now/SUBMISSION_COMMANDS.md` |
| S10 | Required demo report artifacts exist and are packet-verified. | `artifacts/demo/3min-offline/harness/report.md`, `artifacts/demo/3min-offline/harness/report.json`, `dist/portal-submission/portal-submission-verify-latest.txt` |
| S11 | Required bundles/evidence archives exist for submission. | `dist/submission-bundle.zip`, `dist/release-evidence-20260310T122842Z.tar.gz`, `RELEASE_PACKAGE_INDEX.md` |
| S12 | Pre-submit checks and submit-now checks pass. | `dist/submission-readiness-latest.txt`, `dist/pre-submit-verify-latest.txt`, `dist/portal-submission/portal-submission-verify-latest.txt`, `docs/evidence/submit-now/SUBMIT_NOW_INDEX.md` |
| S13 | Freeze/drift evidence is tracked for final submit control. | `dist/submission-freeze/submission-freeze-latest.md`, `dist/submission-freeze/submission-freeze-latest.json`, `dist/submission-freeze/drift-verify-latest.md`, `dist/submission-freeze/drift-verify-latest.json` |

## Cross-links

- Executive digest: `EXEC_HANDOFF_DIGEST.md`
- Ready board: `READY_TO_SUBMIT_STATUS.md`
- Portal manifest: `PORTAL_SUBMISSION_MANIFEST.md`
- Release package index: `RELEASE_PACKAGE_INDEX.md`
