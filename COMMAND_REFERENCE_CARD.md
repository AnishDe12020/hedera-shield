# HederaShield Command Reference Card

Use from repo root for final submission operations.

## Pre-Submit

```bash
./scripts/submission-readiness.sh
./scripts/pre_submit_guard.sh
./scripts/pre-submit-verify.py
```

## Final Submit Prep

```bash
./scripts/generate-portal-submission-packet.py
./scripts/verify-portal-submission-packet.py
./scripts/print_submit_now.sh
./scripts/submission-freeze.py
./scripts/verify-submission-freeze.py
python3 scripts/generate-submit-now-packet.py
```

## Post-Submit Verification

```bash
git rev-parse HEAD
git status --short
./scripts/verify-submission-freeze.py
./scripts/print_submit_now.sh
```

## Related Docs

- [SUBMISSION_TERMINAL_CHECKLIST.md](SUBMISSION_TERMINAL_CHECKLIST.md)
- [SUBMIT_CONTROL_SHEET.md](SUBMIT_CONTROL_SHEET.md)
- [EXEC_HANDOFF_DIGEST.md](EXEC_HANDOFF_DIGEST.md)
