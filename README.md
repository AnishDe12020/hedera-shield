# 🛡️ HederaShield

**AI-powered on-chain compliance agent for Hedera Token Service**

HederaShield is a real-time compliance monitoring system built natively on Hedera. It watches HTS token transfers via the Mirror Node API, applies configurable rule-based and AI-powered analysis to detect suspicious activity, publishes immutable audit logs to HCS, and can automatically enforce actions (freeze, wipe, KYC revoke) through Hedera SDK.

Built for the **Hedera Apex Hackathon 2026**.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        HederaShield                             │
│                                                                 │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐  │
│  │  Mirror Node  │───▶│  Scanner Module   │───▶│  Compliance  │  │
│  │  REST API     │    │                  │    │  Engine      │  │
│  │              │    │  • Token xfers   │    │              │  │
│  │  /api/v1/    │    │  • HBAR xfers    │    │  8 Rules:    │  │
│  │  transactions│    │  • NFT xfers     │    │  • Large TX  │  │
│  │  accounts    │    │  • Pagination    │    │  • Velocity  │  │
│  │  tokens      │    │  • Retry+Backoff │    │  • Sanctions │  │
│  │  topics      │    │                  │    │  • Round Num │  │
│  └──────────────┘    └──────────────────┘    │  • Rapid     │  │
│                                              │  • Structure │  │
│  ┌──────────────┐    ┌──────────────────┐    │  • Dormant   │  │
│  │  Claude AI   │◀───│  AI Analyzer     │◀───│  • Wash Trd  │  │
│  │  (Anthropic) │    │                  │    │              │  │
│  │              │───▶│  Risk scoring    │    └──────┬───────┘  │
│  │  Contextual  │    │  NL explanations │           │          │
│  │  analysis    │    │  Action recs     │           ▼          │
│  └──────────────┘    └──────────────────┘    ┌──────────────┐  │
│                                              │  Alerts      │  │
│  ┌──────────────┐    ┌──────────────────┐    │  Database    │  │
│  │  Hedera SDK  │◀───│  Enforcer        │◀───┤              │  │
│  │              │    │                  │    └──────┬───────┘  │
│  │  TokenFreeze │    │  • Freeze accts  │           │          │
│  │  TokenWipe   │    │  • Wipe tokens   │           ▼          │
│  │  TokenRevoke │    │  • Revoke KYC    │    ┌──────────────┐  │
│  │  KYC         │    │  • Dry-run mode  │    │  HCS Reporter│  │
│  └──────────────┘    └──────────────────┘    │              │  │
│                                              │  Immutable   │  │
│  ┌──────────────┐    ┌──────────────────┐    │  audit trail │  │
│  │  FastAPI     │───▶│  Dashboard       │    │  on-chain    │  │
│  │  REST API    │    │  (Single-page)   │    └──────────────┘  │
│  │              │    │                  │                       │
│  │  /alerts     │    │  Real-time view  │                       │
│  │  /rules      │    │  of alerts,      │                       │
│  │  /enforce    │    │  rules, and      │                       │
│  │  /status     │    │  enforcement     │                       │
│  └──────────────┘    └──────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

## Features

### 🔍 Real-Time Monitoring
- Polls Hedera Mirror Node REST API for HTS token transfers, HBAR transfers, and NFT movements
- Automatic pagination across large result sets
- Exponential backoff retry on transient failures (429, 5xx)
- Configurable polling interval

### 📋 8 Compliance Rules
| Rule | Description | Default Severity |
|------|-------------|-----------------|
| **Large Transfer** | Flags transfers exceeding configurable threshold (per-token overrides) | HIGH |
| **Velocity Check** | Detects excessive transfer frequency from a single account | MEDIUM |
| **Sanctioned Address** | Matches sender/receiver against OFAC-style sanctions list | CRITICAL |
| **Round Number** | Flags suspiciously round-number transfers (structuring indicator) | MEDIUM |
| **Rapid Succession** | Detects bot-driven rapid-fire transfers within seconds | HIGH |
| **Structuring (Anti-Smurfing)** | Catches transfers clustered just below reporting threshold | HIGH |
| **Dormant Account Reactivation** | Flags sudden activity from long-inactive accounts | MEDIUM |
| **Cross-Token Wash Trading** | Detects same-pair transfers across multiple token IDs | HIGH |

### 🤖 AI-Powered Analysis
- Uses Claude (Anthropic) for contextual risk scoring
- Natural language explanations of flagged transactions
- Adaptive risk assessment with recommended enforcement actions
- Graceful fallback when AI is unavailable

### ⚡ Automated Enforcement (HTS-Native)
- **Freeze** accounts via `TokenFreezeTransaction`
- **Wipe** tokens via `TokenWipeTransaction`
- **Revoke KYC** via `TokenRevokeKycTransaction`
- Dry-run mode by default for safety
- Full Hedera SDK integration

### 📝 Immutable Audit Trail (HCS)
- Publishes every compliance alert to an HCS topic
- Creates tamper-proof, timestamped audit log on the Hedera public ledger
- Fetchable via Mirror Node for dashboard display
- JSON-structured messages with version field for schema evolution

### 🖥️ Real-Time Dashboard
- Single-page web app with auto-refresh (10s)
- Alert severity badges, risk score bars, expandable details
- Rule management (add/remove/toggle via UI)
- Enforcement action panel
- Transaction browser with Mirror Node integration
- Dark theme, responsive design

### ⚙️ Configuration
- YAML-based rule configuration with hot-reload
- Per-token threshold overrides
- External sanctions list file support
- Environment-based settings (12-factor app)

## Quick Start

### Prerequisites
- Python 3.12+
- Hedera testnet account ([portal.hedera.com](https://portal.hedera.com))
- Anthropic API key (optional, for AI analysis)

### Option A: Docker (Recommended)

```bash
git clone https://github.com/your-username/hedera-shield.git
cd hedera-shield

cp .env.example .env
# Edit .env with your credentials

docker compose up --build
```

### Option B: Local Setup

```bash
git clone https://github.com/your-username/hedera-shield.git
cd hedera-shield

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your credentials

# Run the API server
python -m hedera_shield.api
```

Open **http://localhost:8000** for the dashboard.

### Run Tests

```bash
# Unit tests (no network required)
pytest tests/ -v

# Include integration tests against testnet Mirror Node
HEDERA_SHIELD_RUN_INTEGRATION=1 pytest tests/ -v
```

### One-Command Judge Evidence Bundle

```bash
# Safe default (credential-free, non-destructive)
./scripts/release-evidence.sh

# Optional: include real testnet artifacts only with explicit opt-in
HEDERA_SHIELD_ENABLE_REAL_TESTNET=1 \
./scripts/release-evidence.sh --env-file .env.testnet --include-real-testnet
```

Default command behavior:
- Runs `ruff check hedera_shield/ tests/`
- Runs `pytest tests/ -v --tb=short`
- Runs mock harness (`scripts/run-integration-harness.sh --mode mock`)
- Builds `dist/submission-bundle.zip`
- Emits `dist/release-evidence-<timestamp>.tar.gz` with logs + artifacts + submission zip

### Submission Readiness + Sync (DNS/Offline Safe)

```bash
# 1) Verify docs/demo/artifacts readiness
./scripts/submission-readiness.sh

# 2) Attempt sync + push with bounded retry/backoff and status report
./scripts/sync-and-submit.sh --max-retries 3 --initial-backoff-seconds 2 --max-backoff-seconds 16

# 3) If push is blocked by DNS/network outage, create offline handoff package
./scripts/offline-handoff.sh

# 4) Generate a single handoff index for judges (markdown + json)
./scripts/generate-handoff-index.py

# Optional: deterministic timestamp/output path
./scripts/generate-handoff-index.py --timestamp "$(date -u +%Y%m%dT%H%M%SZ)" --output-base-dir artifacts/handoff-index
```

Outputs:
- `dist/submission-readiness-latest.txt` (PASS/FAIL checklist summary)
- `dist/sync-submit-status-latest.txt` (pending commits + remote reachability + exact push error when push fails)
- `artifacts/offline-handoff/<timestamp>/handoff-summary.txt`
- `artifacts/offline-handoff/<timestamp>/branch-status.txt`
- `artifacts/offline-handoff/<timestamp>/commit-list.txt`
- `artifacts/offline-handoff/<timestamp>/offline.bundle`
- `artifacts/offline-handoff/<timestamp>/patches/*.patch`
- `artifacts/offline-handoff/<timestamp>/RESTORE_APPLY.md`
- `artifacts/handoff-index/<timestamp>/handoff-index.md`
- `artifacts/handoff-index/<timestamp>/handoff-index.json`

Judge-focused docs:
- [docs/DEMO_RECORDING_RUNBOOK.md](docs/DEMO_RECORDING_RUNBOOK.md) for deterministic 3-minute recording flow (offline-safe default).
- [docs/FINAL_SUBMISSION_CHECKLIST.md](docs/FINAL_SUBMISSION_CHECKLIST.md) for final portal submission checklist and evidence gating.
- [docs/TESTNET_SETUP.md](docs/TESTNET_SETUP.md) for full testnet setup/runbook details.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HEDERA_SHIELD_HEDERA_NETWORK` | Network: testnet, mainnet, previewnet | `testnet` |
| `HEDERA_SHIELD_HEDERA_OPERATOR_ID` | Operator account ID | — |
| `HEDERA_SHIELD_HEDERA_OPERATOR_KEY` | Operator private key | — |
| `HEDERA_SHIELD_MIRROR_NODE_URL` | Mirror Node base URL | testnet URL |
| `HEDERA_SHIELD_LARGE_TRANSFER_THRESHOLD` | Amount threshold for large transfer rule | `10000` |
| `HEDERA_SHIELD_VELOCITY_MAX_TRANSFERS` | Max transfers in velocity window | `50` |
| `HEDERA_SHIELD_MONITORED_TOKEN_IDS` | JSON array of token IDs to monitor | `[]` |
| `HEDERA_SHIELD_SANCTIONED_ADDRESSES` | JSON array of sanctioned addresses | `[]` |
| `HEDERA_SHIELD_ANTHROPIC_API_KEY` | Anthropic API key for Claude AI | — |

### Rules Configuration

Edit `config/rules.yaml` to customize rule parameters, enable/disable rules, and set per-token overrides. See the file for detailed documentation of each rule.

## Demo Walkthrough

### 1. Start the System
```bash
docker compose up --build
# or: python -m hedera_shield.api
```

### 2. View Dashboard
Open http://localhost:8000 — see the live dashboard with status, alerts, and rules.

### 3. Check Rules
```bash
curl http://localhost:8000/rules | python -m json.tool
```

### 4. Fetch Testnet Transactions
```bash
curl "http://localhost:8000/transactions?token_id=0.0.YOUR_TOKEN&limit=10" | python -m json.tool
```

### 5. Run Alert Simulation
```bash
python demo/simulate_alerts.py
```

### 6. Test Enforcement (Dry Run)
```bash
curl -X POST http://localhost:8000/enforce \
  -H "Content-Type: application/json" \
  -d '{"action": "freeze", "token_id": "0.0.5555", "account_id": "0.0.1111"}'
```
Response: `{"status": "dry_run", ...}` — no real blockchain action in dry-run mode.

### 7. Resolve Alerts
```bash
# List alerts
curl http://localhost:8000/alerts | python -m json.tool

# Resolve one
curl -X POST http://localhost:8000/alerts/{ALERT_ID}/resolve
```

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard UI |
| `/health` | GET | Health check |
| `/status` | GET | System status and stats |
| `/alerts` | GET | List alerts (optional `?unresolved_only=true`) |
| `/alerts/{id}/resolve` | POST | Resolve an alert |
| `/rules` | GET | List compliance rules |
| `/rules` | POST | Add a new rule |
| `/rules/{id}` | DELETE | Remove a rule |
| `/transactions` | GET | Fetch transfers from Mirror Node |
| `/enforce` | POST | Execute enforcement action |
| `/docs` | GET | Interactive API docs (Swagger) |

## Project Structure

```
hedera-shield/
├── hedera_shield/
│   ├── __init__.py          # Package init, logging setup
│   ├── api.py               # FastAPI REST API + dashboard serving
│   ├── compliance.py        # 8-rule compliance engine
│   ├── scanner.py           # Mirror Node poller (tokens, HBAR, NFTs)
│   ├── enforcer.py          # HTS enforcement (freeze/wipe/KYC)
│   ├── hcs_reporter.py      # HCS audit trail publisher
│   ├── ai_analyzer.py       # Claude AI risk analysis
│   ├── config.py            # Environment-based settings
│   ├── models.py            # Pydantic data models
│   ├── rules_config.py      # YAML rule loader
│   ├── logging_config.py    # Structured JSON logging
│   └── static/
│       └── dashboard.html   # Single-page dashboard
├── config/
│   ├── rules.yaml           # Compliance rule configuration
│   └── sanctions.txt        # OFAC-style sanctions list
├── tests/
│   ├── test_compliance.py   # Compliance engine tests
│   ├── test_scanner.py      # Scanner tests (mocked HTTP)
│   ├── test_api.py          # API endpoint tests
│   ├── test_new_rules.py    # New rules + HCS tests
│   └── test_integration_testnet.py  # Live testnet tests
├── demo/
│   ├── simulate_alerts.py   # Alert simulation script
│   ├── walkthrough.md       # Demo walkthrough guide
│   └── sample_alerts.json   # Sample alert data
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Tech Stack

- **Python 3.12+** with type hints and async/await
- **FastAPI** — REST API framework
- **Pydantic v2** — data validation and serialization
- **httpx** — async HTTP client for Mirror Node
- **Hedera SDK** — native HTS operations (freeze, wipe, KYC)
- **Anthropic Claude** — AI-powered risk analysis
- **PyYAML** — configuration management
- **pytest + pytest-asyncio** — test framework
- **Docker** — containerized deployment

## License

MIT

---

*Built with ❤️ for the Hedera ecosystem*
