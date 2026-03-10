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
./scripts/sync-and-submit.sh --max-retries 3 --initial-backoff-seconds 2 --max-backoff-seconds 16
./scripts/generate-handoff-index.py
```

## DNS/Network Outage Fallback (Offline Handoff)
- [ ] If sync/push fails, run: `./scripts/offline-handoff.sh`
- [ ] Handoff output directory exists: `artifacts/offline-handoff/<timestamp>/`
- [ ] Handoff summary exists: `artifacts/offline-handoff/<timestamp>/handoff-summary.txt`
- [ ] Bundle exists: `artifacts/offline-handoff/<timestamp>/offline.bundle`
- [ ] Patch series exists: `artifacts/offline-handoff/<timestamp>/patches/*.patch`
- [ ] Restore/apply instructions exist: `artifacts/offline-handoff/<timestamp>/RESTORE_APPLY.md`
- [ ] Summary contains exact push failure text when present in `dist/sync-submit-status-latest.txt`
- [ ] Judge handoff index exists: `artifacts/handoff-index/<timestamp>/handoff-index.md`
- [ ] Judge handoff json exists: `artifacts/handoff-index/<timestamp>/handoff-index.json`

## Submission Notes
- [ ] Notes to judges added in `SUBMISSION.md`
- [ ] Any known limitations disclosed
