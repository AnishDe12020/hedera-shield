# HederaShield Submission Form Draft Pack

Use these as concise, copy-paste-ready entries in the Hackathon form.

## Problem Statement
Teams issuing and operating tokens on Hedera need continuous compliance monitoring across HTS transfers, HBAR movement, and NFT activity. Manual review does not scale, and off-chain audit logs are weak for regulator-facing evidence. Most generic blockchain tools are not built to use Hedera-native enforcement controls.

## Solution Summary
HederaShield is an AI-assisted, Hedera-native compliance agent. It ingests live activity from Mirror Node APIs, evaluates each event with configurable rules and contextual AI scoring, and emits alerts with recommended actions. When enabled, it can execute HTS-native enforcement (freeze, wipe, revoke KYC) and records alerts to HCS for immutable audit evidence.

## Architecture (Short Form)
1. Scanner polls Mirror Node transaction/account/topic APIs with pagination and retry.
2. Compliance engine applies eight built-in rules (large transfer, velocity, sanctions, round number, rapid succession, structuring, dormant reactivation, cross-token wash trading).
3. AI analyzer adds contextual risk explanation and action recommendations.
4. Enforcer maps approved actions to Hedera SDK transactions (freeze, wipe, revoke KYC).
5. HCS reporter writes structured alert payloads to topic messages for tamper-evident logging.
6. FastAPI + dashboard expose alerts, rules, and status for operators and judges.

## Innovation / Differentiation
- Hedera-native enforcement: uses HTS primitives directly rather than contract-only controls.
- Detection plus response: the system can act, not only alert.
- Immutable compliance trail: HCS messages provide ordered, timestamped public audit evidence.
- Offline-safe judging path: deterministic mock harness, reproducible artifact bundle, and readiness checks for non-destructive demonstrations.

## Setup and Run Steps (Judge-Friendly)
```bash
# 1) Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2) Validate quality gate
ruff check hedera_shield/ tests/
pytest tests/ -v --tb=short

# 3) Build evidence bundle (offline-safe default)
./scripts/release-evidence.sh

# 4) Verify submission readiness
./scripts/pre_submit_guard.sh
./scripts/submission-readiness.sh

# 5) Final pre-submit verifier for draft-referenced docs/artifacts
./scripts/pre-submit-verify.py
```

## Required Evidence Referenced By This Draft
- Docs: `README.md`, `SUBMISSION.md`, `docs/DEMO_RECORDING_RUNBOOK.md`, `docs/DEMO_NARRATION_3MIN.md`, `docs/FINAL_SUBMISSION_CHECKLIST.md`, `docs/TESTNET_SETUP.md`, `docs/TESTNET_EVIDENCE.md`, `docs/DEPLOY_PROOF.md`.
- Demo artifacts: `artifacts/demo/3min-offline/harness/{report.md,report.json,harness.log,smoke.log,validator.log}`.
- Bundle artifacts: `dist/submission-bundle.zip`, `artifacts/demo/3min-offline/submission-bundle.zip.sha256`, `dist/release-evidence-*.tar.gz`.
- Validation outputs: `dist/submission-readiness-latest.txt`, `dist/pre-submit-verify-latest.txt`.
- Release final gate: `RELEASE_READINESS.md`.

## Optional Real-Testnet Proof (Only If Explicitly Enabled)
```bash
HEDERA_SHIELD_ENABLE_REAL_TESTNET=1 \
./scripts/run-integration-harness.sh --mode real --env-file .env.testnet --artifacts-dir artifacts/demo/3min-real
```
