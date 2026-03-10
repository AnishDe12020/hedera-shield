# HederaShield Human Handoff Playbook

Generated UTC: 20260310T191604Z
Workspace: /home/anish/hedera-shield
Readiness Gate: **BLOCKED**

## Gate Summary

- Required artifacts complete: 12/12
- Open blockers: 2
- Demo video URL: TODO_ADD_DEMO_VIDEO_URL
- Portal submission URL: UNSET

## Blockers

- [ ] Demo video URL is not set (missing_demo_video_url)
  - Details: Demo video URL is still placeholder/empty.
  - Resolution: Record + upload demo video, then rerun with --demo-video-url <public-or-unlisted-url>.
- [ ] Portal submission URL is not set (missing_portal_submission_url)
  - Details: Portal submission URL for proof capture is empty/placeholder.
  - Resolution: Set --portal-submission-url once final portal form is open.

## Completed Checks

- [x] Demo recording runbook (PASS)
  - Path: /home/anish/hedera-shield/docs/DEMO_RECORDING_RUNBOOK.md
  - Details: found /home/anish/hedera-shield/docs/DEMO_RECORDING_RUNBOOK.md
- [x] Demo narration script (PASS)
  - Path: /home/anish/hedera-shield/docs/DEMO_NARRATION_3MIN.md
  - Details: found /home/anish/hedera-shield/docs/DEMO_NARRATION_3MIN.md
- [x] Submission form draft pack (PASS)
  - Path: /home/anish/hedera-shield/docs/SUBMISSION_FORM_DRAFT_PACK.md
  - Details: found /home/anish/hedera-shield/docs/SUBMISSION_FORM_DRAFT_PACK.md
- [x] Final submission checklist (PASS)
  - Path: /home/anish/hedera-shield/docs/FINAL_SUBMISSION_CHECKLIST.md
  - Details: found /home/anish/hedera-shield/docs/FINAL_SUBMISSION_CHECKLIST.md
- [x] Offline demo harness report (markdown) (PASS)
  - Path: /home/anish/hedera-shield/artifacts/demo/3min-offline/harness/report.md
  - Details: found /home/anish/hedera-shield/artifacts/demo/3min-offline/harness/report.md
- [x] Offline demo harness report (json) (PASS)
  - Path: /home/anish/hedera-shield/artifacts/demo/3min-offline/harness/report.json
  - Details: found /home/anish/hedera-shield/artifacts/demo/3min-offline/harness/report.json
- [x] Submission bundle checksum (PASS)
  - Path: /home/anish/hedera-shield/artifacts/demo/3min-offline/submission-bundle.zip.sha256
  - Details: found /home/anish/hedera-shield/artifacts/demo/3min-offline/submission-bundle.zip.sha256
- [x] Submission bundle zip (PASS)
  - Path: /home/anish/hedera-shield/dist/submission-bundle.zip
  - Details: found /home/anish/hedera-shield/dist/submission-bundle.zip
- [x] Portal packet markdown (PASS)
  - Path: /home/anish/hedera-shield/dist/portal-submission/portal-submission-packet-latest.md
  - Details: found /home/anish/hedera-shield/dist/portal-submission/portal-submission-packet-latest.md
- [x] Portal packet json (PASS)
  - Path: /home/anish/hedera-shield/dist/portal-submission/portal-submission-packet-latest.json
  - Details: found /home/anish/hedera-shield/dist/portal-submission/portal-submission-packet-latest.json
- [x] Submission readiness report (PASS)
  - Path: /home/anish/hedera-shield/dist/submission-readiness-latest.txt
  - Details: found /home/anish/hedera-shield/dist/submission-readiness-latest.txt
- [x] Pre-submit verify report (PASS)
  - Path: /home/anish/hedera-shield/dist/pre-submit-verify-latest.txt
  - Details: found /home/anish/hedera-shield/dist/pre-submit-verify-latest.txt
- [x] Submission freeze manifest (PASS)
  - Path: /home/anish/hedera-shield/dist/submission-freeze/submission-freeze-latest.json
  - Details: found /home/anish/hedera-shield/dist/submission-freeze/submission-freeze-latest.json
- [x] Submission drift verify (PASS)
  - Path: /home/anish/hedera-shield/dist/submission-freeze/drift-verify-latest.json
  - Details: found /home/anish/hedera-shield/dist/submission-freeze/drift-verify-latest.json
- [x] Release evidence tarball (PASS)
  - Path: /home/anish/hedera-shield/dist/release-evidence-20260310T122842Z.tar.gz
  - Details: found /home/anish/hedera-shield/dist/release-evidence-20260310T122842Z.tar.gz

## Execution Plan

### Step 1: Record and Upload Final Demo
Status: **PENDING**
Owner: Anish
Objective: Produce final demo video and capture public/unlisted URL.

Checklist:
- [ ] Open runbook and narration side-by-side.
- [ ] Record 3-minute walkthrough using offline-safe evidence flow.
- [ ] Upload video and store URL in notes.
- [ ] Re-run generator with --demo-video-url once uploaded (current: TODO_ADD_DEMO_VIDEO_URL).

Commands:
```bash
cat '/home/anish/hedera-shield/docs/DEMO_RECORDING_RUNBOOK.md'
cat '/home/anish/hedera-shield/docs/DEMO_NARRATION_3MIN.md'
./scripts/submission-readiness.sh
```

Required absolute paths:
- /home/anish/hedera-shield/docs/DEMO_RECORDING_RUNBOOK.md
- /home/anish/hedera-shield/docs/DEMO_NARRATION_3MIN.md
- /home/anish/hedera-shield/artifacts/demo/3min-offline/harness/report.md
- /home/anish/hedera-shield/artifacts/demo/3min-offline/harness/report.json

### Step 2: Fill Hackathon Portal Form
Status: **PENDING**
Owner: Anish
Objective: Copy finalized technical content and evidence links into portal fields.

Checklist:
- [ ] Open latest portal submission packet markdown.
- [ ] Paste title/description/architecture/innovation/setup fields.
- [ ] Paste repository URL and commit SHA from packet.
- [ ] Paste demo video URL and bundle evidence details.

Commands:
```bash
./scripts/generate-portal-submission-packet.py
./scripts/verify-portal-submission-packet.py
cat '/home/anish/hedera-shield/dist/portal-submission/portal-submission-packet-latest.md'
```

Required absolute paths:
- /home/anish/hedera-shield/dist/portal-submission/portal-submission-packet-latest.md
- /home/anish/hedera-shield/dist/portal-submission/portal-submission-packet-latest.json
- /home/anish/hedera-shield/docs/SUBMISSION_FORM_DRAFT_PACK.md
- /home/anish/hedera-shield/dist/submission-bundle.zip
- /home/anish/hedera-shield/artifacts/demo/3min-offline/submission-bundle.zip.sha256

### Step 3: Final Portal Submit and Proof Capture
Status: **BLOCKED**
Owner: Anish
Objective: Submit final entry and preserve submission proof + push state.

Checklist:
- [ ] Open portal URL and submit final form (current: unset).
- [ ] Capture confirmation page screenshot and URL.
- [ ] Run sync/push best-effort and store status artifact if push fails.
- [ ] Regenerate this handoff playbook for final state snapshot.

Commands:
```bash
./scripts/sync-and-submit.sh --max-retries 3 --initial-backoff-seconds 2 --max-backoff-seconds 16
./scripts/network-recovery-push-runner.sh --check-interval-seconds 30 --max-checks 20
./scripts/generate-human-handoff-playbook.py
```

Required absolute paths:
- /home/anish/hedera-shield/docs/FINAL_SUBMISSION_CHECKLIST.md
- /home/anish/hedera-shield/dist/submission-readiness-latest.txt
- /home/anish/hedera-shield/dist/pre-submit-verify-latest.txt
