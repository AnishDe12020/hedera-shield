# HederaShield Portal Dry-Run Transcript

Dry-run timestamp (UTC): `2026-03-12T10:17:16Z`  
Mode: manual simulation, docs-only, no live portal submit

## Scope and Linked Controls

- [SUBMISSION_HANDOFF_MATRIX.md](SUBMISSION_HANDOFF_MATRIX.md)
- [SUBMIT_OWNER_QUICK_CARD.md](SUBMIT_OWNER_QUICK_CARD.md)
- [SUBMISSION_SEAL_NOTE.md](SUBMISSION_SEAL_NOTE.md)
- [OPERATOR_SIGNOFF_BRIEF.md](OPERATOR_SIGNOFF_BRIEF.md)
- [EXEC_HANDOFF_DIGEST.md](EXEC_HANDOFF_DIGEST.md)
- [SUBMIT_CONTROL_SHEET.md](SUBMIT_CONTROL_SHEET.md)
- [READY_TO_SUBMIT_STATUS.md](READY_TO_SUBMIT_STATUS.md)
- [PORTAL_SUBMISSION_MANIFEST.md](PORTAL_SUBMISSION_MANIFEST.md)
- Source packet: `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json`

## Pre-Submit Command Transcript (Expected PASS)

```bash
./scripts/submission-readiness.sh
# expect: READINESS|summary|PASS

./scripts/pre_submit_guard.sh
# expect: GUARD|PASS|pre-submit guard complete (demo-id=3min-offline)

./scripts/print_submit_now.sh
# expect: required submit-now paths all CHECK|PASS
```

Checkpoint: all three commands return PASS summary lines before manual portal entry starts.

## Manual Portal Entry Transcript (Simulated)

1. Prompt: `Project Title`  
   Answer: `HederaShield: Hedera-Native AI Compliance Agent`  
   Confirm: title matches packet canonical value.

2. Prompt: `Short Description`  
   Answer: `AI-assisted, Hedera-native compliance monitoring and enforcement for HTS tokens with immutable HCS audit evidence.`  
   Confirm: no wording drift from packet.

3. Prompt: `Full Description`  
   Answer source: `fields.full_description` in packet JSON  
   Confirm: pasted exactly, no manual edits.

4. Prompt: `Architecture`  
   Answer source: `fields.architecture` in packet JSON  
   Confirm: pasted exactly.

5. Prompt: `Innovation / Differentiation`  
   Answer source: `fields.innovation` in packet JSON  
   Confirm: pasted exactly.

6. Prompt: `Setup / Repro Instructions`  
   Answer source: `fields.setup` in packet JSON  
   Confirm: fenced command block preserved.

7. Prompt: `Demo Walkthrough Steps`  
   Answer source: `fields.demo_steps` in packet JSON  
   Confirm: step numbering preserved.

8. Prompt: `Judging Highlights`  
   Answer source: `fields.judging_highlights` in packet JSON  
   Confirm: bullet/ordering preserved.

9. Prompt: `Repository URL`  
   Answer: `https://github.com/AnishDe12020/hedera-shield`  
   Confirm: URL resolves publicly.

10. Prompt: `Commit SHA`  
    Answer: output of `git rev-parse HEAD` at click time  
    Confirm: SHA in form equals local SHA exactly.

11. Prompt: `Branch`  
    Answer: `master`  
    Confirm: matches active submit branch.

12. Prompt: `Demo Video URL`  
    Expected action: replace `TODO_ADD_DEMO_VIDEO_URL` with final public link  
    Confirm: no placeholder remains.

13. Prompt: `Deployed URL`  
    Expected action: replace `TODO_ADD_FINAL_DEPLOYED_URL_OR_NA` with final public URL or `N/A`  
    Confirm: no placeholder remains.

14. Prompt: `Submit`  
    Expected action: click once after final review  
    Confirm: capture confirmation screenshot + UTC timestamp immediately.

## Final Confirmation Checkpoints

- [ ] PASS chain confirmed for readiness + guard + submit-now checks.
- [ ] All portal fields copied from packet JSON or exact fixed values above.
- [ ] Placeholder values replaced (`DEMO_VIDEO_URL`, `DEPLOYED_URL_OR_NA`).
- [ ] Portal SHA equals local `git rev-parse HEAD` at submit click time.
- [ ] Confirmation screenshot and UTC timestamp recorded in sprint evidence.
