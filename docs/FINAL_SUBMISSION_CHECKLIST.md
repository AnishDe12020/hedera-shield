# HederaShield Final Submission Checklist

Use this as the final gate before hackathon portal submission.

## Submission Metadata
- [ ] Team name: `<FILL_TEAM_NAME>`
- [ ] Primary contact: `<FILL_NAME_AND_EMAIL>`
- [ ] Repository URL: `<PASTE_REPO_URL>`
- [ ] Commit SHA submitted: `<PASTE_GIT_SHA>`
- [ ] Hackathon portal submission URL: `<PASTE_PORTAL_URL>`
- [ ] Demo video URL (public/unlisted): `<PASTE_VIDEO_URL>`
- [ ] Optional live deployment URL: `<PASTE_DEPLOYMENT_URL_OR_NA>`

## Required Evidence Artifacts
- [ ] Demo runbook used: `docs/DEMO_RECORDING_RUNBOOK.md`
- [ ] Demo narration script ready: `docs/DEMO_NARRATION_3MIN.md`
- [ ] Submission form draft pack ready: `docs/SUBMISSION_FORM_DRAFT_PACK.md`
- [ ] Offline demo artifacts directory exists: `artifacts/demo/3min-offline/`
- [ ] Harness outputs exist:
  - [ ] `artifacts/demo/3min-offline/harness/report.md`
  - [ ] `artifacts/demo/3min-offline/harness/report.json`
  - [ ] `artifacts/demo/3min-offline/harness/harness.log`
  - [ ] `artifacts/demo/3min-offline/harness/smoke.log`
  - [ ] `artifacts/demo/3min-offline/harness/validator.log`
- [ ] Bundle outputs exist:
  - [ ] `dist/submission-bundle.zip`
  - [ ] `artifacts/demo/3min-offline/submission-bundle.zip.sha256`
- [ ] Testnet docs included:
  - [ ] `docs/TESTNET_SETUP.md`
  - [ ] `docs/TESTNET_EVIDENCE.md`
  - [ ] `docs/DEPLOY_PROOF.md`

## Optional Real-Testnet Evidence (Only If Used)
- [ ] Real opt-in command recorded (`HEDERA_SHIELD_ENABLE_REAL_TESTNET=1`)
- [ ] Real harness artifact directory: `artifacts/demo/3min-real/`
- [ ] Real harness summary line shows PASS in logs

## Final Verification Commands
```bash
ruff check hedera_shield/ tests/
pytest tests/ -v --tb=short
./scripts/package-submission.sh
./scripts/submission-readiness.sh
./scripts/pre-submit-verify.py
./scripts/generate-portal-submission-packet.py
./scripts/verify-portal-submission-packet.py
./scripts/submission-freeze.py
./scripts/verify-submission-freeze.py
./scripts/sprint-multi-repo-dashboard.py
./scripts/sprint-multi-repo-dashboard.py --repo-config config/sprint-repos.json
./scripts/sprint-multi-repo-dashboard.py --attempt-push
./scripts/sync-and-submit.sh --max-retries 3 --initial-backoff-seconds 2 --max-backoff-seconds 16
./scripts/network-recovery-push-runner.sh --check-interval-seconds 30 --max-checks 20
./scripts/generate-handoff-index.py
./scripts/final-handoff-export.sh
```

## DNS/Network Outage Fallback (Offline Handoff)
- [ ] Multi-repo dashboard markdown exists: `dist/sprint-status/sprint-dashboard-latest.md`
- [ ] Multi-repo dashboard json exists: `dist/sprint-status/sprint-dashboard-latest.json`
- [ ] Dashboard captures per-repo branch/ahead-behind/latest-commit/remote reachability
- [ ] Dashboard captures exact push failure text when `--attempt-push` is used and push fails
- [ ] Optional safe dry-run works: `./scripts/network-recovery-push-runner.sh --dry-run --check-interval-seconds 15 --max-checks 4`
- [ ] Runner text status exists: `dist/network-recovery-push-status-latest.txt`
- [ ] Runner JSON status exists: `dist/network-recovery-push-status-latest.json`
- [ ] Runner status captures exact push/network error text when push fails
- [ ] Submission-freeze latest markdown exists: `dist/submission-freeze/submission-freeze-latest.md`
- [ ] Submission-freeze latest json exists: `dist/submission-freeze/submission-freeze-latest.json`
- [ ] Drift verify latest markdown exists: `dist/submission-freeze/drift-verify-latest.md`
- [ ] Drift verify latest json exists: `dist/submission-freeze/drift-verify-latest.json`
- [ ] If sync/push fails, run: `./scripts/offline-handoff.sh`
- [ ] Handoff output directory exists: `artifacts/offline-handoff/<timestamp>/`
- [ ] Handoff summary exists: `artifacts/offline-handoff/<timestamp>/handoff-summary.txt`
- [ ] Bundle exists: `artifacts/offline-handoff/<timestamp>/offline.bundle`
- [ ] Patch series exists: `artifacts/offline-handoff/<timestamp>/patches/*.patch`
- [ ] Restore/apply instructions exist: `artifacts/offline-handoff/<timestamp>/RESTORE_APPLY.md`
- [ ] Summary contains exact push failure text when present in `dist/sync-submit-status-latest.txt`
- [ ] Judge handoff index exists: `artifacts/handoff-index/<timestamp>/handoff-index.md`
- [ ] Judge handoff json exists: `artifacts/handoff-index/<timestamp>/handoff-index.json`
- [ ] Cross-repo final handoff package exists: `dist/final-handoff/final-handoff-<timestamp>/`
- [ ] Cross-repo master index markdown exists: `dist/final-handoff/final-handoff-<timestamp>/master-index.md`
- [ ] Cross-repo master index json exists: `dist/final-handoff/final-handoff-<timestamp>/master-index.json`
- [ ] Cross-repo latest markdown alias exists: `dist/final-handoff/final-handoff-latest.md`
- [ ] Cross-repo latest json alias exists: `dist/final-handoff/final-handoff-latest.json`

## Submission Notes
- [ ] Notes to judges added in `SUBMISSION.md`
- [ ] Any known limitations disclosed
