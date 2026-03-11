# HederaShield Apex Submission Checklist

Use this as the last-mile gate for Hedera Apex portal submission.

## 1) Submission Metadata

- [ ] Team name: `<TEAM_NAME>`
- [ ] Project name: `HederaShield`
- [ ] Primary contact (name + email): `<CONTACT_NAME_EMAIL>`
- [ ] Repository URL: `<REPO_URL>`
- [ ] Commit SHA to submit: `<GIT_SHA>`
- [ ] Apex portal entry URL: `<APEX_PORTAL_SUBMISSION_URL>`

## 2) Required Public Links

- [ ] Demo video (public/unlisted): `<DEMO_VIDEO_URL>`
- [ ] Source code repository: `<REPO_URL>`
- [ ] Optional deployment URL: `<DEPLOYMENT_URL_OR_NA>`
- [ ] Optional docs landing page: `<DOCS_URL_OR_NA>`

## 3) Required Local Artifacts

- [ ] Demo narration script exists: `DEMO_SCRIPT.md`
- [ ] Submission checklist exists: `SUBMISSION_CHECKLIST.md`
- [ ] Smoke verifier exists: `scripts/smoke.sh`
- [ ] Submission write-up exists: `SUBMISSION.md`
- [ ] Packaged bundle exists: `dist/submission-bundle.zip`

## 4) Fast Verification Steps

- [ ] Run smoke verification:
  ```bash
  ./scripts/smoke.sh
  ```
- [ ] Run lint:
  ```bash
  ruff check hedera_shield/ tests/
  ```
- [ ] Run tests:
  ```bash
  pytest tests/ -v --tb=short
  ```
- [ ] Build bundle:
  ```bash
  ./scripts/package-submission.sh
  ```

## 5) Evidence for Judges

- [ ] Mock harness report: `artifacts/demo/smoke-local/harness/report.md`
- [ ] Mock harness JSON: `artifacts/demo/smoke-local/harness/report.json`
- [ ] Smoke logs (if generated): `artifacts/demo/smoke-local/*.log`
- [ ] Any optional real-testnet evidence clearly marked as opt-in

## 6) Final Apex Portal Pass

- [ ] Paste final project summary from `SUBMISSION.md`
- [ ] Attach required links above
- [ ] Verify repo visibility/access from judge perspective
- [ ] Verify submitted SHA matches the final committed state
- [ ] Submit and archive confirmation screenshot/URL

## 7) Final Sign-Off

- [ ] No placeholder values remain in portal form fields
- [ ] Demo script timing stays within 3-5 minutes
- [ ] Team agrees this exact commit is the final submission state
