# Hedera Apex Portal Submission Packet

Generated UTC: 20260312T045355Z

## Copy-Paste Fields

- Title: HederaShield: Hedera-Native AI Compliance Agent
- Short description: AI-assisted, Hedera-native compliance monitoring and enforcement for HTS tokens with immutable HCS audit evidence.

### Full description
Teams issuing and operating tokens on Hedera need continuous compliance monitoring across HTS transfers, HBAR movement, and NFT activity. Manual review does not scale, and off-chain audit logs are weak for regulator-facing evidence. Most generic blockchain tools are not built to use Hedera-native enforcement controls.

HederaShield is an AI-assisted, Hedera-native compliance agent. It ingests live activity from Mirror Node APIs, evaluates each event with configurable rules and contextual AI scoring, and emits alerts with recommended actions. When enabled, it can execute HTS-native enforcement (freeze, wipe, revoke KYC) and records alerts to HCS for immutable audit evidence.

### Architecture
1. Scanner polls Mirror Node transaction/account/topic APIs with pagination and retry.
2. Compliance engine applies eight built-in rules (large transfer, velocity, sanctions, round number, rapid succession, structuring, dormant reactivation, cross-token wash trading).
3. AI analyzer adds contextual risk explanation and action recommendations.
4. Enforcer maps approved actions to Hedera SDK transactions (freeze, wipe, revoke KYC).
5. HCS reporter writes structured alert payloads to topic messages for tamper-evident logging.
6. FastAPI + dashboard expose alerts, rules, and status for operators and judges.

### Innovation
- Hedera-native enforcement: uses HTS primitives directly rather than contract-only controls.
- Detection plus response: the system can act, not only alert.
- Immutable compliance trail: HCS messages provide ordered, timestamped public audit evidence.
- Offline-safe judging path: deterministic mock harness, reproducible artifact bundle, and readiness checks for non-destructive demonstrations.

### Setup
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

### Demo steps
- 0:00-0:20 Setup deterministic artifact paths
  Command:
  export DEMO_ID="3min-offline"
  export DEMO_DIR="artifacts/demo/${DEMO_ID}"
  Expected result:
  - `artifacts/demo/3min-offline/` exists and is empty.
- 0:20-1:20 Run integration harness in mock mode (no network)
  Command:
  ./scripts/run-integration-harness.sh \
  --mode mock \
  --env-file .env.testnet.example \
  --artifacts-dir "$DEMO_DIR/harness" \
  Expected output markers:
  Expected artifacts:
  - `artifacts/demo/3min-offline/harness/harness.log`
  - `artifacts/demo/3min-offline/harness/validator.log`
  - `artifacts/demo/3min-offline/harness/smoke.log`
  - `artifacts/demo/3min-offline/harness/integration.log`
  - `artifacts/demo/3min-offline/harness/report.md`
  - `artifacts/demo/3min-offline/harness/report.json`
  - `artifacts/demo/3min-offline/harness.stdout.log`
- 1:20-2:00 Build submission bundle
  Command:
  ./scripts/package-submission.sh | tee "$DEMO_DIR/package.stdout.log"
  Expected output markers:
  Expected artifacts:
  - `dist/submission-bundle.zip`
  - `artifacts/demo/3min-offline/package.stdout.log`
- 2:00-2:20 Record immutable checksum for the bundle
  Command:
  sha256sum dist/submission-bundle.zip | tee "$DEMO_DIR/submission-bundle.zip.sha256"
  Expected output pattern:
  Expected artifact:
  - `artifacts/demo/3min-offline/submission-bundle.zip.sha256`
- 2:20-3:00 Show final evidence tree
  Command:
  find "$DEMO_DIR" -maxdepth 2 -type f | sort
  Expected output list (order deterministic from `sort`):

### Judging highlights
- HTS-native enforcement actions: freeze, wipe, revoke KYC.
- HCS-backed immutable compliance audit trail.
- Mirror Node-driven monitoring across HTS, HBAR, and NFTs.
- Offline-safe deterministic demo workflow with reproducible artifacts.
- Deeper integration details are documented in `SUBMISSION.md` under Hedera-Specific Integrations.

## Links

- Repository URL: https://github.com/AnishDe12020/hedera-shield
- Commit SHA: db3254f0b85cb05f1fe120175b1665beaf69a992
- Branch: master
- Demo video URL: TODO_ADD_DEMO_VIDEO_URL
- Deployed URL: TODO_ADD_FINAL_DEPLOYED_URL_OR_NA
- Demo report markdown: `artifacts/demo/3min-offline/harness/report.md`
- Demo report json: `artifacts/demo/3min-offline/harness/report.json`
- Submission bundle: `dist/submission-bundle.zip`
- Release evidence bundle: `dist/release-evidence-20260310T122842Z.tar.gz`

## Referenced Paths

- `README.md`
- `SUBMISSION.md`
- `docs/SUBMISSION_FORM_DRAFT_PACK.md`
- `docs/DEMO_RECORDING_RUNBOOK.md`
- `docs/DEMO_NARRATION_3MIN.md`
- `docs/FINAL_SUBMISSION_CHECKLIST.md`
- `docs/TESTNET_SETUP.md`
- `docs/TESTNET_EVIDENCE.md`
- `docs/DEPLOY_PROOF.md`
- `artifacts/demo/3min-offline/harness/report.md`
- `artifacts/demo/3min-offline/harness/report.json`
- `dist/submission-bundle.zip`
- `dist/release-evidence-20260310T122842Z.tar.gz`
