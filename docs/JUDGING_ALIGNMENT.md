# HederaShield Judging Alignment

This map ties common hackathon judging criteria to concrete HederaShield artifacts for fast reviewer verification.

## 1) Problem Clarity and Relevance
- Criteria focus: clear problem definition, real-world need, and target users.
- Primary artifacts:
  - `README.md` (problem framing + system scope)
  - `SUBMISSION.md` (judge-facing narrative and value proposition)
  - `HEDERA_PORTAL_SUBMISSION_PACKET.md` sections 1, 2, and 6

## 2) Technical Depth and Quality
- Criteria focus: architecture quality, implementation rigor, reproducibility.
- Primary artifacts:
  - `README.md` (architecture + components)
  - `hedera_shield/` (core implementation)
  - `tests/` (automated validation coverage)
  - `scripts/release-evidence.sh` (deterministic build/test/package flow)

## 3) Hedera Integration Quality
- Criteria focus: meaningful use of Hedera primitives, integration realism.
- Primary artifacts:
  - `docs/TESTNET_SETUP.md` (operator setup + execution path)
  - `docs/TESTNET_EVIDENCE.md` (captured testnet evidence)
  - `docs/DEPLOY_PROOF.md` (deployment and runtime proof)
  - `HEDERA_TESTNET_RUNBOOK.md` (live integration/operator runbook)

## 4) AI / Agent Usage
- Criteria focus: clear, justified AI usage with operator controls.
- Primary artifacts:
  - `HEDERA_PORTAL_SUBMISSION_PACKET.md` section 4
  - `README.md` (AI analyzer overview)
  - `scripts/submission-readiness.sh` and `scripts/pre-submit-verify.py` (agentic automation for readiness checks)

## 5) Demo Quality and Reproducibility
- Criteria focus: understandable demo, deterministic reproduction path.
- Primary artifacts:
  - `docs/DEMO_RECORDING_RUNBOOK.md`
  - `docs/DEMO_NARRATION_3MIN.md`
  - `artifacts/demo/3min-offline/harness/report.md`
  - `artifacts/demo/3min-offline/harness/report.json`

## 6) Submission Completeness and Reviewer Experience
- Criteria focus: easy verification, complete links, transparent limitations.
- Primary artifacts:
  - `docs/FINAL_SUBMISSION_CHECKLIST.md`
  - `docs/SUBMISSION_FORM_DRAFT_PACK.md`
  - `dist/portal-submission/portal-submission-packet-latest.md`
  - `dist/portal-submission/portal-submission-verify-latest.txt`
  - `docs/KNOWN_ISSUES_AND_WORKAROUNDS.md`

## 7) Final Judge Quick Path
Use this order for rapid validation:
1. `HEDERA_PORTAL_SUBMISSION_PACKET.md`
2. `docs/FINAL_SUBMISSION_CHECKLIST.md`
3. `docs/JUDGING_ALIGNMENT.md`
4. `dist/portal-submission/portal-submission-verify-latest.txt`
