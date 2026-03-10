# HederaShield 3-Minute Demo Recording Runbook

Purpose: deterministic, offline-safe demo flow for hackathon judging.

## Scope
- Default mode is offline-safe (mock harness, no live testnet probe).
- Real testnet commands are listed separately and are opt-in only.

## 3-Minute Script (Offline-Safe Default)

### 0:00-0:20 Setup deterministic artifact paths
```bash
export DEMO_ID="3min-offline"
export DEMO_DIR="artifacts/demo/${DEMO_ID}"
rm -rf "$DEMO_DIR"
mkdir -p "$DEMO_DIR"
```

Expected result:
- `artifacts/demo/3min-offline/` exists and is empty.

### 0:20-1:20 Run integration harness in mock mode (no network)
```bash
./scripts/run-integration-harness.sh \
  --mode mock \
  --env-file .env.testnet.example \
  --artifacts-dir "$DEMO_DIR/harness" \
  | tee "$DEMO_DIR/harness.stdout.log"
```

Expected output markers:
```text
HARNESS|mode|PASS|running mode=mock
HARNESS|validator|PASS|env file format accepted
HARNESS|smoke|PASS|smoke checks passed
HARNESS|summary|PASS|harness checks passed
```

Expected artifacts:
- `artifacts/demo/3min-offline/harness/harness.log`
- `artifacts/demo/3min-offline/harness/validator.log`
- `artifacts/demo/3min-offline/harness/smoke.log`
- `artifacts/demo/3min-offline/harness/integration.log`
- `artifacts/demo/3min-offline/harness/report.md`
- `artifacts/demo/3min-offline/harness/report.json`
- `artifacts/demo/3min-offline/harness.stdout.log`

### 1:20-2:00 Build submission bundle
```bash
./scripts/package-submission.sh | tee "$DEMO_DIR/package.stdout.log"
```

Expected output markers:
```text
PACKAGE|required_files|PASS|all required files present
PACKAGE|bundle|PASS|created /.../dist/submission-bundle.zip with <N> files
```

Expected artifacts:
- `dist/submission-bundle.zip`
- `artifacts/demo/3min-offline/package.stdout.log`

### 2:00-2:20 Record immutable checksum for the bundle
```bash
sha256sum dist/submission-bundle.zip | tee "$DEMO_DIR/submission-bundle.zip.sha256"
```

Expected output pattern:
```text
<sha256_hex>  dist/submission-bundle.zip
```

Expected artifact:
- `artifacts/demo/3min-offline/submission-bundle.zip.sha256`

### 2:20-3:00 Show final evidence tree
```bash
find "$DEMO_DIR" -maxdepth 2 -type f | sort
```

Expected output list (order deterministic from `sort`):
```text
artifacts/demo/3min-offline/harness.stdout.log
artifacts/demo/3min-offline/harness/harness.log
artifacts/demo/3min-offline/harness/integration.log
artifacts/demo/3min-offline/harness/report.json
artifacts/demo/3min-offline/harness/report.md
artifacts/demo/3min-offline/harness/smoke.log
artifacts/demo/3min-offline/harness/validator.log
artifacts/demo/3min-offline/package.stdout.log
artifacts/demo/3min-offline/submission-bundle.zip.sha256
```

## Optional Real-Testnet Add-On (Opt-In Only)

Prerequisites:
- `.env.testnet` populated with non-placeholder testnet operator credentials
- `HEDERA_SHIELD_ENABLE_REAL_TESTNET=1` explicitly set

Command:
```bash
HEDERA_SHIELD_ENABLE_REAL_TESTNET=1 \
./scripts/run-integration-harness.sh \
  --mode real \
  --env-file .env.testnet \
  --artifacts-dir artifacts/demo/3min-real \
  | tee artifacts/demo/3min-real.stdout.log
```

Expected additional output markers:
```text
HARNESS|real_opt_in|PASS|explicit real mode opt-in enabled
HARNESS|real_network|PASS|network is testnet
HARNESS|real_creds|PASS|operator credentials look non-placeholder
HARNESS|summary|PASS|harness checks passed
```
