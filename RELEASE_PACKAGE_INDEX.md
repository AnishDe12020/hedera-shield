# HederaShield Release Package Index

Index timestamp (UTC): `2026-03-12T07:11:49Z`
Branch: `master`

## Final control documents

| File | Purpose |
| --- | --- |
| [PRE_SUBMIT_RECAP.md](PRE_SUBMIT_RECAP.md) | Final quick validation, guard, and operator pre-submit recap. |
| [PORTAL_READY_HANDOFF.md](PORTAL_READY_HANDOFF.md) | Final portal-ready operator sequence, required files, and pre-submit sanity checks. |
| [SUBMISSION_READY_SNAPSHOT.md](SUBMISSION_READY_SNAPSHOT.md) | Submission-ready state snapshot and referenced evidence paths. |
| [PORTAL_SUBMISSION_MANIFEST.md](PORTAL_SUBMISSION_MANIFEST.md) | Portal field mapping and final manual submission guardrails. |
| [SUBMISSION_PACKET_VERIFIED.md](SUBMISSION_PACKET_VERIFIED.md) | Verification log for packet/readiness/submit-now checks. |
| [ZERO_DRIFT_VERIFICATION.md](ZERO_DRIFT_VERIFICATION.md) | Freeze-manifest drift verification and lock confirmation. |
| [RELEASE_READINESS.md](RELEASE_READINESS.md) | Release readiness status and operator checklist. |
| [RELEASE_CANDIDATE_LOCK.md](RELEASE_CANDIDATE_LOCK.md) | Candidate lock details, integrity hashes, and handoff steps. |
| [SUBMISSION_FREEZE.md](SUBMISSION_FREEZE.md) | Submission freeze procedure and frozen artifact references. |

## Portal submission packet

| File | Purpose |
| --- | --- |
| [docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json](docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json) | Source-of-truth portal copy/paste payload. |
| [HEDERA_PORTAL_SUBMISSION_PACKET.md](HEDERA_PORTAL_SUBMISSION_PACKET.md) | Human-readable fallback for portal packet contents. |
| [docs/evidence/submit-now/SUBMIT_NOW_INDEX.md](docs/evidence/submit-now/SUBMIT_NOW_INDEX.md) | Submit-now evidence index for manual operator use. |
| [docs/evidence/submit-now/SUBMISSION_COMMANDS.md](docs/evidence/submit-now/SUBMISSION_COMMANDS.md) | Exact final command sequence for operator execution. |

## Generated verification artifacts

| File | Purpose |
| --- | --- |
| [dist/submission-readiness-latest.txt](dist/submission-readiness-latest.txt) | Latest readiness summary report (`READINESS|summary|PASS`). |
| [dist/pre-submit-verify-latest.txt](dist/pre-submit-verify-latest.txt) | Latest pre-submit verification summary (`VERIFY|summary|PASS`). |
| [dist/portal-submission/portal-submission-packet-latest.md](dist/portal-submission/portal-submission-packet-latest.md) | Rendered latest portal submission packet. |
| [dist/portal-submission/portal-submission-verify-latest.txt](dist/portal-submission/portal-submission-verify-latest.txt) | Latest portal packet verification summary (`PORTAL_VERIFY|summary|PASS`). |
| [dist/submission-freeze/submission-freeze-latest.md](dist/submission-freeze/submission-freeze-latest.md) | Latest freeze manifest (human-readable). |
| [dist/submission-freeze/submission-freeze-latest.json](dist/submission-freeze/submission-freeze-latest.json) | Latest freeze manifest (machine-readable). |
| [dist/submission-freeze/drift-verify-latest.md](dist/submission-freeze/drift-verify-latest.md) | Latest drift verification report (`DRIFT|summary|PASS`). |
| [dist/submission-freeze/drift-verify-latest.json](dist/submission-freeze/drift-verify-latest.json) | Latest drift verification report (machine-readable). |

## Demo evidence artifacts

| File | Purpose |
| --- | --- |
| [artifacts/demo/3min-offline/harness/report.md](artifacts/demo/3min-offline/harness/report.md) | Human-readable demo harness report. |
| [artifacts/demo/3min-offline/harness/report.json](artifacts/demo/3min-offline/harness/report.json) | Machine-readable demo harness report. |
| [artifacts/demo/3min-offline/harness/harness.log](artifacts/demo/3min-offline/harness/harness.log) | Harness execution log. |
| [artifacts/demo/3min-offline/harness/smoke.log](artifacts/demo/3min-offline/harness/smoke.log) | Smoke test log. |
| [artifacts/demo/3min-offline/harness/validator.log](artifacts/demo/3min-offline/harness/validator.log) | Environment validator output log. |
| [artifacts/demo/3min-offline/submission-bundle.zip.sha256](artifacts/demo/3min-offline/submission-bundle.zip.sha256) | Submission bundle checksum proof. |

## Release bundles

| File | Purpose |
| --- | --- |
| [dist/submission-bundle.zip](dist/submission-bundle.zip) | Packaged project bundle for submission handoff. |
| [dist/release-evidence-20260310T122842Z.tar.gz](dist/release-evidence-20260310T122842Z.tar.gz) | Timestamped evidence archive used in release validation. |
| [artifacts/integration/release-20260310T122842Z/release-report.md](artifacts/integration/release-20260310T122842Z/release-report.md) | Integration release report (human-readable). |
| [artifacts/integration/release-20260310T122842Z/release-report.json](artifacts/integration/release-20260310T122842Z/release-report.json) | Integration release report (machine-readable). |
