# HederaShield Judge Handoff Index

- Timestamp (UTC): `20260310T150932Z`
- Generated at (UTC): `2026-03-10T15:09:32+00:00`
- Overall status: `READY`
- Summary counts: PASS=15 WARN=0 FAIL=0

## Key Links
- `release_bundle_latest`: `dist/release-evidence-20260310T122842Z.tar.gz`
- `integration_release_dir_latest`: `artifacts/integration/release-20260310T122842Z`
- `offline_handoff_dir_latest`: `artifacts/offline-handoff/20260310T160000Z`
- `demo_runbook`: `docs/DEMO_RECORDING_RUNBOOK.md`
- `final_submission_checklist`: `docs/FINAL_SUBMISSION_CHECKLIST.md`

## Artifact Status
| Key | Required | Status | Path | Details |
|---|---|---|---|---|
| `release_bundle_latest` | `no` | `PASS` | `dist/release-evidence-20260310T122842Z.tar.gz` | found dist/release-evidence-20260310T122842Z.tar.gz |
| `integration_release_dir_latest` | `no` | `PASS` | `artifacts/integration/release-20260310T122842Z` | found artifacts/integration/release-20260310T122842Z |
| `integration_release_report_md` | `no` | `PASS` | `artifacts/integration/release-20260310T122842Z/release-report.md` | found artifacts/integration/release-20260310T122842Z/release-report.md |
| `integration_release_report_json` | `no` | `PASS` | `artifacts/integration/release-20260310T122842Z/release-report.json` | found artifacts/integration/release-20260310T122842Z/release-report.json |
| `integration_mock_report_md` | `no` | `PASS` | `artifacts/integration/release-20260310T122842Z/mock/report.md` | found artifacts/integration/release-20260310T122842Z/mock/report.md |
| `integration_mock_report_json` | `no` | `PASS` | `artifacts/integration/release-20260310T122842Z/mock/report.json` | found artifacts/integration/release-20260310T122842Z/mock/report.json |
| `offline_handoff_dir_latest` | `no` | `PASS` | `artifacts/offline-handoff/20260310T160000Z` | found artifacts/offline-handoff/20260310T160000Z |
| `offline_handoff_summary` | `no` | `PASS` | `artifacts/offline-handoff/20260310T160000Z/handoff-summary.txt` | found artifacts/offline-handoff/20260310T160000Z/handoff-summary.txt |
| `offline_handoff_bundle` | `no` | `PASS` | `artifacts/offline-handoff/20260310T160000Z/offline.bundle` | found artifacts/offline-handoff/20260310T160000Z/offline.bundle |
| `offline_handoff_restore` | `no` | `PASS` | `artifacts/offline-handoff/20260310T160000Z/RESTORE_APPLY.md` | found artifacts/offline-handoff/20260310T160000Z/RESTORE_APPLY.md |
| `demo_runbook` | `yes` | `PASS` | `docs/DEMO_RECORDING_RUNBOOK.md` | found docs/DEMO_RECORDING_RUNBOOK.md |
| `final_submission_checklist` | `yes` | `PASS` | `docs/FINAL_SUBMISSION_CHECKLIST.md` | found docs/FINAL_SUBMISSION_CHECKLIST.md |
| `submission_readiness_latest` | `no` | `PASS` | `dist/submission-readiness-latest.txt` | found dist/submission-readiness-latest.txt |
| `sync_submit_latest` | `no` | `PASS` | `dist/sync-submit-status-latest.txt` | found dist/sync-submit-status-latest.txt |
| `git_push_status_latest` | `no` | `PASS` | `dist/git-push-status-latest.txt` | found dist/git-push-status-latest.txt |

## Sync/Push Error Context
### PUSH_FINAL_ERROR
```text
ssh: Could not resolve hostname github.com: Temporary failure in name resolution
fatal: Could not read from remote repository.
```
### GIT_PUSH_ERROR
```text
Timestamp UTC: 2026-03-10T15:09:27Z
Command: git push origin HEAD

ssh: Could not resolve hostname github.com: Temporary failure in name resolution
fatal: Could not read from remote repository.

Please make sure you have the correct access rights
and the repository exists.
```
