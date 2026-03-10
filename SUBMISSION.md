# HederaShield — Hackathon Submission

## Hedera Apex Hackathon 2026

---

## Project Description

**HederaShield** is an AI-powered, on-chain compliance agent purpose-built for the Hedera Token Service (HTS). It provides real-time monitoring, rule-based and AI-driven analysis, automated enforcement, and immutable audit logging — everything a regulated entity needs to stay compliant while operating on Hedera.

### The Problem

Token issuers, exchanges, and financial institutions operating on Hedera need automated compliance monitoring. Manual review doesn't scale. Off-chain solutions lose the audit trail. Existing blockchain analytics tools aren't Hedera-native — they don't leverage HTS's built-in freeze, wipe, and KYC operations.

### The Solution

HederaShield deeply integrates with Hedera's native services:

1. **Monitors** HTS token transfers, HBAR movements, and NFTs via the Mirror Node REST API
2. **Analyzes** every transaction against 8 configurable compliance rules + AI-powered risk scoring
3. **Enforces** automatically via HTS-native operations (freeze account, wipe tokens, revoke KYC)
4. **Logs** every compliance decision to HCS for an immutable, tamper-proof audit trail
5. **Visualizes** everything through a real-time dashboard

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.12+ (async/await, type hints) |
| **API Framework** | FastAPI |
| **Data Validation** | Pydantic v2 |
| **HTTP Client** | httpx (async, with retry + exponential backoff) |
| **Hedera Integration** | Hedera SDK (enforcement), Mirror Node REST API (monitoring) |
| **AI** | Anthropic Claude (contextual risk analysis) |
| **Configuration** | PyYAML, pydantic-settings (12-factor app) |
| **Testing** | pytest, pytest-asyncio (44 tests, 6 integration tests) |
| **Deployment** | Docker, Docker Compose |
| **CI** | GitHub Actions |

---

## Hedera-Specific Integrations

### 1. Hedera Token Service (HTS)

HederaShield is built specifically for HTS tokens. It understands the HTS transaction model and leverages HTS-native enforcement capabilities:

- **TokenFreezeTransaction** — Freeze a suspicious account's token balance, preventing further transfers
- **TokenWipeTransaction** — Remove tokens from a compromised account (requires wipe key)
- **TokenRevokeKycTransaction** — Revoke KYC status, blocking the account from token operations

These are *not* smart contract calls — they're native Hedera operations that are fast, cheap ($0.001), and final.

### 2. Mirror Node REST API

The scanner module polls the Mirror Node for real-time transaction data:

- `/api/v1/transactions` — HTS token transfers, HBAR transfers, NFT movements
- `/api/v1/accounts/{id}/tokens` — Account token balances
- `/api/v1/transactions/{id}` — Transaction detail lookup
- `/api/v1/topics/{id}/messages` — HCS audit trail retrieval

Features: automatic pagination, exponential backoff retry (429/5xx), configurable polling interval.

### 3. Hedera Consensus Service (HCS)

Every compliance alert is published to an HCS topic as a JSON message, creating an **immutable, timestamped audit trail** on the Hedera public ledger. This provides:

- **Tamper-proof records** — No one can alter or delete compliance logs after submission
- **Public verifiability** — Regulators can independently verify the audit trail via Mirror Node
- **Schema versioning** — Messages include a version field for forward compatibility
- **Cheap archival** — HCS messages cost ~$0.0001 each

### 4. Hedera SDK

Native Hedera SDK integration for operator-level actions:

- Client initialization for mainnet/testnet/previewnet
- Operator key management
- Transaction submission and receipt handling
- Dry-run mode for safe testing

---

## Compliance Rules (8 Built-In)

| # | Rule | What It Catches | Severity |
|---|------|----------------|----------|
| 1 | Large Transfer | Transfers exceeding configurable thresholds | HIGH |
| 2 | Velocity Check | Abnormal transfer frequency from a single account | MEDIUM |
| 3 | Sanctioned Address | Interaction with OFAC-listed or blocked addresses | CRITICAL |
| 4 | Round Number | Suspiciously round amounts (structuring indicator) | MEDIUM |
| 5 | Rapid Succession | Bot-driven rapid-fire transfers within seconds | HIGH |
| 6 | Structuring (Anti-Smurfing) | Transfers clustered just below reporting threshold | HIGH |
| 7 | Dormant Account | Sudden activity from long-inactive accounts | MEDIUM |
| 8 | Cross-Token Wash Trading | Same-pair transfers across multiple token IDs | HIGH |

All rules are configurable via YAML, support per-token overrides, and can be added/removed dynamically via API.

---

## Prize Track Justification

### Best Use of Hedera Technology

HederaShield demonstrates deep, idiomatic use of multiple Hedera services:

- **HTS** — Not just monitoring tokens, but using HTS's *native* freeze/wipe/KYC as enforcement primitives. This isn't possible on EVM chains without custom smart contracts.
- **HCS** — Using consensus service for what it's best at: creating immutable, ordered audit logs. Each compliance decision is cryptographically timestamped by the Hedera network.
- **Mirror Node** — Full utilization of the REST API with pagination, retry logic, and multi-entity monitoring (tokens, HBAR, NFTs).
- **SDK** — Direct integration with the Hedera SDK for operator-level enforcement actions.

### DeFi / Financial Services Track

Compliance monitoring is a critical infrastructure need for:
- Token issuers (stablecoin operators, security token platforms)
- Decentralized exchanges operating on Hedera
- Financial institutions using HTS for asset tokenization
- DAOs and treasuries managing multi-token portfolios

HederaShield provides the compliance layer that makes institutional adoption of Hedera tokens viable.

---

## What Makes This Different

1. **Hedera-Native** — Not a generic blockchain analytics tool ported to Hedera. Built from the ground up for HTS/HCS/Mirror Node.

2. **AI + Rules** — Combines deterministic rule-based checks (fast, explainable) with AI-powered analysis (contextual, adaptive). Best of both worlds.

3. **Enforcement, Not Just Detection** — Most compliance tools stop at alerting. HederaShield can actually *enforce* — freezing accounts and revoking access through HTS-native operations.

4. **Immutable Audit Trail** — Every compliance decision is logged to HCS, not a database. Regulators get a tamper-proof record on the public ledger.

5. **Production-Ready** — Docker deployment, structured logging, comprehensive test suite (44 tests), CI pipeline, configurable rules, dry-run safety mode.

---

## Running the Demo

```bash
# Clone and setup
git clone https://github.com/your-username/hedera-shield.git
cd hedera-shield
cp .env.example .env
# Edit .env with testnet credentials

# Start
docker compose up --build

# Open dashboard
open http://localhost:8000

# Run simulation
python demo/simulate_alerts.py
```

---

## Testnet Runbook + Evidence Checklist

### Runbook

```bash
# 1) Prepare testnet env
cp .env.testnet.example .env.testnet

# 2a) Mock/demo harness (safe default, credentials optional)
./scripts/run-integration-harness.sh --mode mock --env-file .env.testnet

# 2b) Real testnet harness (explicit opt-in + non-placeholder creds)
HEDERA_SHIELD_ENABLE_REAL_TESTNET=1 \
./scripts/run-integration-harness.sh --mode real --env-file .env.testnet

# 3) Start API with testnet config
cp .env.testnet .env
python -m hedera_shield.api

# 4) Verify health endpoint
curl -s http://localhost:8000/health
```

Harness output is machine-readable and expected in this format:

```text
HARNESS|<check_name>|PASS|<details>
HARNESS|<check_name>|FAIL|<details>
HARNESS|summary|PASS|harness checks passed
```

### Evidence Checklist

- Harness artifact bundle under `artifacts/integration/<timestamp>/`:
  - `report.md` and `report.json`
  - `harness.log`, `validator.log`, `smoke.log`, `integration.log`
- Harness output showing summary pass line in selected mode
- API health check response from `GET /health`
- One sample transaction query result (`GET /transactions`)
- Optional: real-mode harness run with integration pytest passing

---

## Test Coverage

```
44 passed, 6 skipped (integration tests require network)

Tests cover:
- All 8 compliance rules (positive + negative cases)
- API endpoints (CRUD for alerts, rules, enforcement)
- Scanner parsing (mocked Mirror Node responses)
- HCS reporter (dry-run publishing, serialization)
- YAML rule configuration loading
```

---

## Team

| Role | Name |
|------|------|
| Developer | *[Your Name]* |
| — | — |

---

## Links

- **Repository**: https://github.com/your-username/hedera-shield
- **Demo Video**: *[link]*
- **Live Dashboard**: *[link if deployed]*

---

*Built for Hedera Apex Hackathon 2026*
