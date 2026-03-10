# HederaShield Testnet Evidence

- Generated (UTC): `2026-03-10T09:43:15Z`
- Capture mode: `DRY_RUN`
- Env file: `.env.testnet.example`
- Network: `testnet`
- Mirror node: `https://testnet.mirrornode.hedera.com`

## Captured Transactions

| tx_id | tx_hash | mirror_link | hashscan_link |
|---|---|---|---|
| `TX_ID_PLACEHOLDER_1` | `N/A` | <https://testnet.mirrornode.hedera.com/api/v1/transactions/TX_ID_PLACEHOLDER_1> | <https://hashscan.io/testnet/transaction/TX_ID_PLACEHOLDER_1> |
| `TX_ID_PLACEHOLDER_2` | `N/A` | <https://testnet.mirrornode.hedera.com/api/v1/transactions/TX_ID_PLACEHOLDER_2> | <https://hashscan.io/testnet/transaction/TX_ID_PLACEHOLDER_2> |

## Reproduction Commands

```bash
cp .env.testnet.example .env.testnet
HEDERA_SHIELD_ENABLE_REAL_TESTNET=1 ./scripts/run-integration-harness.sh --mode real --env-file .env.testnet.example
./scripts/capture-testnet-evidence.sh --env-file .env.testnet.example --output docs/TESTNET_EVIDENCE.md --limit 3
```

## Dry-Run Next Steps

Credentials are missing or placeholders; this file was generated in safe dry-run mode.

Run these exact commands after adding real testnet operator credentials:

```bash
cp .env.testnet.example .env.testnet.example
# edit .env.testnet.example and set non-placeholder HEDERA_SHIELD_HEDERA_OPERATOR_ID / HEDERA_SHIELD_HEDERA_OPERATOR_KEY
HEDERA_SHIELD_ENABLE_REAL_TESTNET=1 ./scripts/run-integration-harness.sh --mode real --env-file .env.testnet.example
./scripts/capture-testnet-evidence.sh --env-file .env.testnet.example --output docs/TESTNET_EVIDENCE.md --limit 3
```
