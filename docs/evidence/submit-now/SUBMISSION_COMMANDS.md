# HederaShield Submission Commands

Use this command sheet to quickly regenerate key submission artifacts before final portal submit.

## 1) Quick Validation + Guard

```bash
./scripts/submission-readiness.sh
./scripts/pre_submit_guard.sh
./scripts/pre-submit-verify.py
```

## 2) Portal Packet + Verification

```bash
./scripts/generate-portal-submission-packet.py
./scripts/verify-portal-submission-packet.py
./scripts/print_submit_now.sh
```

## 3) Freeze Manifest + Drift Verification

```bash
./scripts/submission-freeze.py
./scripts/verify-submission-freeze.py
```

## 4) Rebuild Full Evidence Bundle (if artifacts are stale)

```bash
./scripts/release-evidence.sh
```

Optional (requires valid testnet credentials):

```bash
./scripts/release-evidence.sh --env-file .env.testnet --include-real-testnet
```

## 5) One-Pass Pre-Portal Sequence

```bash
./scripts/submission-readiness.sh \
  && ./scripts/pre_submit_guard.sh \
  && ./scripts/pre-submit-verify.py \
  && ./scripts/generate-portal-submission-packet.py \
  && ./scripts/verify-portal-submission-packet.py \
  && ./scripts/print_submit_now.sh \
  && ./scripts/submission-freeze.py \
  && ./scripts/verify-submission-freeze.py
```
