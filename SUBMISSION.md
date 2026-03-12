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
| **Testing** | pytest, pytest-asyncio (106 automated tests run locally; 6 live integration tests are explicit opt-in) |
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

5. **Production-Ready** — Docker deployment, structured logging, comprehensive test suite (106 automated tests), CI pipeline, configurable rules, dry-run safety mode.

---

## Running the Demo

```bash
# Clone and setup
git clone https://github.com/your-username/hedera-shield.git
cd hedera-shield
cp .env.example .env
# Optional for offline demo: keep placeholder values in .env
# Required for live testnet actions: set real testnet operator credentials

# Start
docker compose up --build

# Open dashboard
open http://localhost:8000

# Run judge-visible offline simulation (sample HTS events -> rules -> HCS dry-run report)
./scripts/run-e2e-simulation.py
```

Generated artifact paths:
- `artifacts/demo/e2e-simulation/<timestamp>/report.json`
- `artifacts/demo/e2e-simulation/<timestamp>/report.md`

---

## Testnet Runbook + Evidence Checklist

Use the dedicated judge-facing docs:

- Final 3-5 minute demo sequence (problem, setup, monitored events, findings, HCS reporting, impact): `DEMO_RUNBOOK.md`
- Deterministic 3-minute demo runbook (offline-safe by default): `docs/DEMO_RECORDING_RUNBOOK.md`
- Timestamped 3-minute narration aligned to runbook artifacts: `docs/DEMO_NARRATION_3MIN.md`
- Copy-paste-ready submission form draft answers: `docs/SUBMISSION_FORM_DRAFT_PACK.md`
- Hackathon form field mapping packet with evidence placeholders: `SUBMISSION_PACKET.md`
- Portal-ready field packet with copy/paste sections: `HEDERA_PORTAL_SUBMISSION_PACKET.md`
- Final portal submission checklist (links + evidence placeholders): `docs/FINAL_SUBMISSION_CHECKLIST.md`
- Fast failure-signature + remediation command reference: `TROUBLESHOOTING_QUICKREF.md`
- Credentials-ready operator handoff runbook with funding/token setup + failure modes: `HEDERA_TESTNET_RUNBOOK.md`
- Full testnet setup and evidence capture reference: `docs/TESTNET_SETUP.md`
- Testnet transaction evidence document: `docs/TESTNET_EVIDENCE.md`

## Submission Execution Commands

Credential markers used below:
- `[NO TESTNET OPERATOR CREDS REQUIRED]` runs safely with placeholders/offline-safe defaults.
- `[TESTNET OPERATOR CREDS REQUIRED]` requires real Hedera testnet operator id/key in `.env.testnet`.

```bash
# 1) Build lint/test/harness/package evidence bundle [NO TESTNET OPERATOR CREDS REQUIRED]
./scripts/release-evidence.sh

# Optional: include real testnet artifacts in release evidence [TESTNET OPERATOR CREDS REQUIRED]
HEDERA_SHIELD_ENABLE_REAL_TESTNET=1 \
./scripts/release-evidence.sh --env-file .env.testnet --include-real-testnet

# 2) Confirm submission readiness state (docs + artifacts + bundle checks) [NO TESTNET OPERATOR CREDS REQUIRED]
./scripts/submission-readiness.sh

# 3) Final draft-linked verifier for required docs/artifacts [NO TESTNET OPERATOR CREDS REQUIRED]
./scripts/pre-submit-verify.py

# 4) Capture immutable submission-freeze snapshot manifest (markdown + json) [NO TESTNET OPERATOR CREDS REQUIRED]
./scripts/submission-freeze.py

# 5) Verify current artifacts/commit state against latest freeze manifest [NO TESTNET OPERATOR CREDS REQUIRED]
./scripts/verify-submission-freeze.py

# 6) Generate consolidated multi-repo sprint push dashboard (read-only default) [NO TESTNET OPERATOR CREDS REQUIRED]
./scripts/sprint-multi-repo-dashboard.py

# Optional: explicit mirrored GitLab/Hedera/DO repo config [NO TESTNET OPERATOR CREDS REQUIRED]
./scripts/sprint-multi-repo-dashboard.py --repo-config config/sprint-repos.json

# Optional: attempt safe push for reachable repos [NO TESTNET OPERATOR CREDS REQUIRED]
./scripts/sprint-multi-repo-dashboard.py --attempt-push

# 7) Sync and push with graceful DNS/offline failure handling + status report [NO TESTNET OPERATOR CREDS REQUIRED]
./scripts/sync-and-submit.sh --max-retries 3 --initial-backoff-seconds 2 --max-backoff-seconds 16

# 8) If still blocked, run periodic network-recovery push runner [NO TESTNET OPERATOR CREDS REQUIRED]
./scripts/network-recovery-push-runner.sh --check-interval-seconds 30 --max-checks 20

# Optional: safe dry-run mode (never pushes) [NO TESTNET OPERATOR CREDS REQUIRED]
./scripts/network-recovery-push-runner.sh --dry-run --check-interval-seconds 15 --max-checks 4

# 9) If push remains blocked by DNS/network outage, export offline handoff package [NO TESTNET OPERATOR CREDS REQUIRED]
./scripts/offline-handoff.sh

# 10) Generate final judge handoff index (markdown + json) [NO TESTNET OPERATOR CREDS REQUIRED]
./scripts/generate-handoff-index.py

# Optional: explicit timestamp for deterministic handoff folder naming [NO TESTNET OPERATOR CREDS REQUIRED]
./scripts/generate-handoff-index.py --timestamp "$(date -u +%Y%m%dT%H%M%SZ)" --output-base-dir artifacts/handoff-index

# 11) Generate final Hedera Apex portal submission packet (markdown + json) [NO TESTNET OPERATOR CREDS REQUIRED]
./scripts/generate-portal-submission-packet.py

# 12) Verify all packet-referenced files/paths exist before portal submission [NO TESTNET OPERATOR CREDS REQUIRED]
./scripts/verify-portal-submission-packet.py

# 13) Export cross-repo final handoff package (read-only across source repos) [NO TESTNET OPERATOR CREDS REQUIRED]
./scripts/final-handoff-export.sh

# 14) Generate execution-ready human handoff playbook (manual final steps + blockers) [NO TESTNET OPERATOR CREDS REQUIRED]
./scripts/generate-human-handoff-playbook.sh

# 15) Capture live testnet transaction evidence doc [TESTNET OPERATOR CREDS REQUIRED]
./scripts/capture-testnet-evidence.sh --env-file .env.testnet --output docs/TESTNET_EVIDENCE.md

# 16) Run live integration harness (Mirror Node probe + integration tests) [TESTNET OPERATOR CREDS REQUIRED]
HEDERA_SHIELD_ENABLE_REAL_TESTNET=1 \
./scripts/run-integration-harness.sh --mode real --env-file .env.testnet
```

Report outputs:
- `dist/submission-readiness-latest.txt`
- `dist/pre-submit-verify-latest.txt`
- `dist/submission-freeze/submission-freeze-latest.md`
- `dist/submission-freeze/submission-freeze-latest.json`
- `dist/submission-freeze/drift-verify-latest.md`
- `dist/submission-freeze/drift-verify-latest.json`
- `dist/sprint-status/sprint-dashboard-<timestamp>.md`
- `dist/sprint-status/sprint-dashboard-<timestamp>.json`
- `dist/sprint-status/sprint-dashboard-latest.md`
- `dist/sprint-status/sprint-dashboard-latest.json`
- `dist/sync-submit-status-latest.txt`
- `dist/network-recovery-push-status-latest.txt`
- `dist/network-recovery-push-status-latest.json`
- `artifacts/offline-handoff/<timestamp>/handoff-summary.txt`
- `artifacts/offline-handoff/<timestamp>/offline.bundle`
- `artifacts/offline-handoff/<timestamp>/patches/*.patch`
- `artifacts/offline-handoff/<timestamp>/RESTORE_APPLY.md`
- `artifacts/handoff-index/<timestamp>/handoff-index.md`
- `artifacts/handoff-index/<timestamp>/handoff-index.json`
- `dist/final-handoff/final-handoff-<timestamp>/master-index.md`
- `dist/final-handoff/final-handoff-<timestamp>/master-index.json`
- `dist/final-handoff/final-handoff-latest.md`
- `dist/final-handoff/final-handoff-latest.json`
- `dist/handoff-playbook/<timestamp>/human-handoff-playbook.md`
- `dist/handoff-playbook/<timestamp>/human-handoff-playbook.json`
- `dist/handoff-playbook/human-handoff-playbook-latest.md`
- `dist/handoff-playbook/human-handoff-playbook-latest.json`

Evidence readiness expectations:
- Offline-safe evidence is complete when `dist/submission-bundle.zip`, `dist/release-evidence-*.tar.gz`, and the latest `dist/*-latest.*` reports exist.
- Live Hedera evidence is complete only after `docs/TESTNET_EVIDENCE.md` is refreshed from non-placeholder credentials and includes real testnet transaction ids with mirror/hashscan links.

---

## Test Coverage

```
Validation snapshot (UTC 2026-03-12T03:10:58Z):
- ruff check hedera_shield/ tests/: All checks passed!
- pytest tests/ -v --tb=short: 100 passed, 6 skipped in 2.13s
- ./scripts/package-submission.sh: PASS, built dist/submission-bundle.zip with 39 files

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
