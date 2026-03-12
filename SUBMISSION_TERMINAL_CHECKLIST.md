# HederaShield Submission Terminal Checklist

Run from repo root in order and require PASS summaries before portal submit.

## 1) Pre-Submit Checks

```bash
./scripts/submission-readiness.sh
./scripts/pre_submit_guard.sh
./scripts/pre-submit-verify.py
```

## 2) Submit-Now Prep

```bash
./scripts/generate-portal-submission-packet.py
./scripts/verify-portal-submission-packet.py
./scripts/print_submit_now.sh
python3 scripts/generate-submit-now-packet.py
```

## 3) Freeze + Drift Lock

```bash
./scripts/submission-freeze.py
./scripts/verify-submission-freeze.py
```

## 4) Post-Submit

```bash
git rev-parse HEAD
git status --short
```

## Related Docs

- [COMMAND_REFERENCE_CARD.md](COMMAND_REFERENCE_CARD.md)
- [SUBMIT_CONTROL_SHEET.md](SUBMIT_CONTROL_SHEET.md)
- [EXEC_HANDOFF_DIGEST.md](EXEC_HANDOFF_DIGEST.md)
