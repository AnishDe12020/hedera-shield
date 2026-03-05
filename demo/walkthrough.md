# HederaShield Demo Walkthrough

## What is HederaShield?

HederaShield is an AI-powered compliance agent for Hedera Token Service (HTS). It monitors token transfers in real-time, detects compliance violations using configurable rules and Claude AI analysis, and can automatically enforce actions like freezing accounts or revoking KYC status.

---

## Setup (2 minutes)

### Option A: Docker (Recommended)

```bash
cp .env.example .env
# Edit .env with your Hedera testnet credentials and Anthropic API key
docker compose up --build
```

### Option B: Local

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env
python -m hedera_shield.api
```

Open http://localhost:8000 for the dashboard.

---

## Demo Script

### 1. System Overview (Dashboard)

Open the dashboard at http://localhost:8000. You'll see:

- **Status bar** showing uptime, monitored tokens, and scan status
- **Alerts panel** (empty initially)
- **Rules panel** showing the 5 built-in compliance rules
- **Enforcement panel** for manual actions

### 2. View Compliance Rules

```bash
curl http://localhost:8000/rules | python -m json.tool
```

Built-in rules:
| Rule | Description |
|------|-------------|
| Large Transfer | Flags transfers > 10,000 tokens |
| Velocity Check | Flags > 50 transfers/hour from one account |
| Sanctioned Address | Flags any interaction with OFAC-listed addresses |
| Round Number | Flags suspiciously round transfers (10000, 50000, etc.) |
| Rapid Succession | Flags multiple transfers within 10 seconds |

### 3. Simulate a Large Transfer Alert

The compliance engine analyzes transfers in real-time. To demonstrate with sample data:

```bash
# Fetch recent testnet transactions
curl "http://localhost:8000/transactions?limit=10" | python -m json.tool
```

### 4. Sanctioned Address Detection

```bash
# Check current alerts (will show any matches against sanctions list)
curl http://localhost:8000/alerts | python -m json.tool
```

Each alert includes:
- Severity level (LOW/MEDIUM/HIGH/CRITICAL)
- Risk score (0.0 - 1.0)
- AI-generated analysis explaining the risk
- Recommended enforcement action

### 5. Enforcement Actions (Dry Run)

```bash
# Freeze a suspicious account (dry-run mode by default)
curl -X POST http://localhost:8000/enforce \
  -H "Content-Type: application/json" \
  -d '{
    "action": "freeze",
    "token_id": "0.0.5555",
    "account_id": "0.0.1111"
  }' | python -m json.tool
```

Response shows `"status": "dry_run"` - no real action taken. In production, this would submit a `TokenFreezeTransaction` to Hedera.

### 6. Resolve an Alert

```bash
# Get alert IDs
curl http://localhost:8000/alerts | python -m json.tool

# Resolve an alert
curl -X POST http://localhost:8000/alerts/{ALERT_ID}/resolve
```

### 7. Add a Custom Rule

```bash
curl -X POST http://localhost:8000/rules \
  -H "Content-Type: application/json" \
  -d '{
    "rule": {
      "id": "rule-custom-whale",
      "name": "Whale Alert",
      "description": "Flag transfers over 1M tokens",
      "alert_type": "large_transfer",
      "severity": "critical",
      "parameters": {"threshold": 1000000}
    }
  }' | python -m json.tool
```

### 8. System Health

```bash
curl http://localhost:8000/health
curl http://localhost:8000/status | python -m json.tool
```

---

## Architecture Highlights

1. **Mirror Node Integration**: Polls Hedera's mirror node REST API for real-time transaction data. Supports token transfers, HBAR transfers, and NFT movements.

2. **Configurable Rules Engine**: YAML-based rule configuration with hot-reload support. Ships with 5 built-in rules, extensible via API or config files.

3. **AI-Powered Analysis**: Uses Claude to perform deep contextual analysis on flagged transactions, providing natural language explanations and risk scores.

4. **Automated Enforcement**: Can freeze accounts, wipe tokens, or revoke KYC via Hedera SDK. Defaults to dry-run mode for safety.

5. **Real-time Dashboard**: Single-page web app with auto-refresh, showing alerts, rules, and enforcement in one view.

---

## Key Differentiators

- **AI + Rules**: Combines deterministic rule-based checks with AI judgment for fewer false positives
- **HTS-Native**: Built specifically for Hedera Token Service with freeze/wipe/KYC support
- **Production-Ready**: Structured logging, Docker deployment, configurable rules, dry-run safety
- **Hackathon-Ready**: Works out of the box with testnet, impressive dashboard, clear demo flow
