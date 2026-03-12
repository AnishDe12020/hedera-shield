# HederaShield Final Submission Checklist

Purpose: complete these steps in order immediately before Hedera Apex portal submission.

## 0) Final Metadata (Fill First)
- [ ] Portal submission URL: `<PASTE_PORTAL_SUBMISSION_URL>`
- [ ] Team name: `<PASTE_TEAM_NAME>`
- [ ] Primary contact (name + email): `<PASTE_CONTACT>`
- [ ] Repository URL: `<PASTE_REPOSITORY_URL>`
- [ ] Final commit SHA to submit: `<PASTE_COMMIT_SHA>`
- [ ] Demo video URL (public/unlisted): `<PASTE_DEMO_VIDEO_URL>`
- [ ] Optional deployed URL: `<PASTE_DEPLOY_URL_OR_NA>`

## 1) Last-Minute Validation (No Feature Changes)
Run:

```bash
./scripts/pre_submit_guard.sh
./scripts/submission-readiness.sh
./scripts/pre-submit-verify.py
./scripts/generate-portal-submission-packet.py
./scripts/verify-portal-submission-packet.py
./scripts/submission-freeze.py
./scripts/verify-submission-freeze.py
```

Gate:
- [ ] `scripts/pre_submit_guard.sh` exits `0`
- [ ] `dist/submission-readiness-latest.txt` shows `READINESS|summary|PASS`
- [ ] `dist/pre-submit-verify-latest.txt` shows `VERIFY|summary|PASS`
- [ ] `dist/portal-submission/portal-submission-verify-latest.txt` shows `PORTAL_VERIFY|summary|PASS`
- [ ] `dist/submission-freeze/submission-freeze-latest.md` exists and references current `HEAD`
- [ ] `./scripts/verify-submission-freeze.py` reports `PASS`

## 2) Demo Video Proof (Portal Requirement)
- [ ] Recorded using `docs/DEMO_RECORDING_RUNBOOK.md`
- [ ] Narration aligned with `docs/DEMO_NARRATION_3MIN.md`
- [ ] Video includes project overview, detection flow, evidence artifacts, and final outcomes
- [ ] Video link pasted in metadata section above

## 3) Repo Pointers To Paste In Portal
- [ ] `README.md`
- [ ] `SUBMISSION.md`
- [ ] `HEDERA_PORTAL_SUBMISSION_PACKET.md`
- [ ] `docs/JUDGING_ALIGNMENT.md`

## 4) Setup Proof (Environment + Hedera/Testnet)
- [ ] Setup runbook: `docs/TESTNET_SETUP.md`
- [ ] Testnet evidence: `docs/TESTNET_EVIDENCE.md`
- [ ] Deploy proof: `docs/DEPLOY_PROOF.md`
- [ ] Submission bundle: `dist/submission-bundle.zip`

## 5) Integration Evidence Placeholders (Fill Exact Paths)
- [ ] Integration summary markdown: `<PASTE_PATH_TO_INTEGRATION_REPORT_MD>`
- [ ] Integration summary JSON: `<PASTE_PATH_TO_INTEGRATION_REPORT_JSON>`
- [ ] Demo harness markdown: `artifacts/demo/3min-offline/harness/report.md`
- [ ] Demo harness JSON: `artifacts/demo/3min-offline/harness/report.json`
- [ ] Release evidence bundle: `<PASTE_PATH_TO_RELEASE_EVIDENCE_TAR_GZ>`

## 6) Known Limitations Disclosure (Required Transparency)
- [ ] Linked/quoted from `docs/KNOWN_ISSUES_AND_WORKAROUNDS.md`
- [ ] Portal "limitations" field filled with current constraints and mitigations
- [ ] Any optional/non-default features clearly labeled as optional in submission text

## 7) Final Portal Form Pass
- [ ] Copy final answer blocks from `HEDERA_PORTAL_SUBMISSION_PACKET.md`
- [ ] Confirm all links open without auth issues
- [ ] Confirm submitted SHA matches metadata SHA
- [ ] Submit in portal

## 8) Post-Submit Snapshot
- [ ] Save submitted portal confirmation screenshot to `<PASTE_LOCAL_PATH>`
- [ ] Save final submitted text export to `<PASTE_LOCAL_PATH>`
- [ ] Record timestamp (UTC): `<PASTE_UTC_TIMESTAMP>`
