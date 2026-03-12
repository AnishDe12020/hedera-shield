# HederaShield Submission Packet (Form Mapping)

Use this file to copy into hackathon portal fields with direct evidence references.

## 1) Project Summary

- Project name: `HederaShield`
- One-liner: AI-assisted, Hedera-native compliance monitoring and audit agent for HTS activity.
- Problem: Token issuers need continuous compliance checks, actionable controls, and immutable regulator-facing audit trails.
- Solution: Mirror Node ingestion + rules/AI risk analysis + enforcement recommendations + HCS audit reporting.

## 2) Differentiators

- Hedera-native enforcement model (HTS-aligned controls, not generic chain heuristics).
- Detection plus response readiness (not alerts-only tooling).
- Immutable audit trail through HCS message reporting.
- Offline-safe deterministic demo path for judging and reproducibility.

## 3) Architecture Bullets

- Scanner: polls/normalizes transaction and token activity inputs.
- Compliance engine: evaluates events against configurable rule set.
- AI analyzer: enriches risk context and action rationale.
- Enforcement layer: maps approved actions to HTS-native operations.
- HCS reporter: emits structured compliance alert payloads for immutable audit history.
- API/dashboard: provides operator/judge-visible status, alerts, and rule management.

## 4) Judging Alignment

- Innovation: Hedera-native compliance stack with integrated HCS audit trail.
- Technical quality: tested Python service with reproducible readiness scripts and validation gates.
- Ecosystem fit: directly uses HTS/HCS/Mirror Node workflows relevant to Hedera token teams.
- Practical impact: reduces compliance response latency and improves audit defensibility.

## 5) Evidence Links / Placeholders

Repository docs:
- `README.md`
- `SUBMISSION.md`
- `DEMO_RUNBOOK.md`
- `docs/DEMO_RECORDING_RUNBOOK.md`
- `docs/DEMO_NARRATION_3MIN.md`
- `docs/SUBMISSION_FORM_DRAFT_PACK.md`
- `docs/FINAL_SUBMISSION_CHECKLIST.md`
- `VALIDATION.md`

Deterministic demo/readiness artifacts:
- `artifacts/demo/3min-offline/harness/report.md`
- `artifacts/demo/3min-offline/harness/report.json`
- `artifacts/demo/3min-offline/harness/harness.log`
- `dist/submission-readiness-latest.txt`
- `dist/pre-submit-verify-latest.txt`
- `dist/submission-bundle.zip`
- `dist/release-evidence-*.tar.gz`

Portal/manual fields to fill:
- Demo video URL: `<PASTE_DEMO_VIDEO_URL>`
- Public repo URL: `<PASTE_REPOSITORY_URL>`
- Optional deployment URL: `<PASTE_DASHBOARD_URL_OR_NA>`
- Team/contact field(s): `<PASTE_TEAM_DETAILS>`

## 6) Ready-to-Submit Checklist

- Summary text aligned to sections 1-4 above.
- Evidence files generated and present under `dist/` + `artifacts/`.
- Demo recording follows `DEMO_RUNBOOK.md` / `docs/DEMO_RECORDING_RUNBOOK.md`.
- Portal field placeholders replaced with final URLs/team info.
