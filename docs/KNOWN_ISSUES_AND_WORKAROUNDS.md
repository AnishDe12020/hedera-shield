# Known Issues and Workarounds

This file tracks current integration blockers and practical mitigations for testnet readiness.

## 1) No direct transaction ingestion endpoint in API

Issue:
- Current API exposes read endpoints (`/transactions`, `/alerts`, `/status`) and enforcement endpoint (`/enforce`), but no dedicated POST endpoint to inject external transaction events.

Impact:
- Integrators cannot push synthetic transactions directly into the compliance engine over REST.

Workaround:
- Use live read path via mirror node through `/transactions` to verify ingestion path.
- Use `demo/simulate_alerts.py` to demonstrate enforcement and expected alert behavior narratives.

## 2) Real on-chain enforcement needs valid operator credentials

Issue:
- `HEDERA_SHIELD_HEDERA_OPERATOR_ID` and `HEDERA_SHIELD_HEDERA_OPERATOR_KEY` placeholders cannot sign Hedera transactions.

Impact:
- Live freeze/wipe/kyc-revoke actions cannot execute on testnet until real credentials are configured.

Workaround:
- Keep dry-run behavior for demos and integration scaffolding.
- Run `./scripts/integration_preflight.sh --env-file .env.testnet` to clearly classify readiness (GREEN/YELLOW/RED) before live attempts.
- For live credential verification, use read-only integration first: `HEDERA_SHIELD_RUN_INTEGRATION=1 pytest -q tests/test_integration_testnet.py`.

## 3) Mirror Node dependency can be intermittently unavailable

Issue:
- Public mirror node endpoints may return transient timeouts/rate limits.

Impact:
- Smoke/integration checks may fail even when local code is correct.

Workaround:
- Re-run smoke checks after a short delay.
- Use the existing retry/backoff logic in scanner-based flows.
- Keep an evidence log by running `./scripts/run-live-integration.sh --env-file .env.testnet` and preserving generated report under `docs/evidence/`.

## 4) Local API health probe may show false-negative if API is not started

Issue:
- Preflight checks probe `http://<api_host>:<api_port>/health`; this fails when API is not running yet.

Impact:
- Readiness can appear `YELLOW` despite valid config.

Workaround:
- Start API (`python -m hedera_shield.api`) before rerunning preflight, or treat this as expected pre-start warning.

## 5) Anthropic key and model may be absent in constrained integration runs

Issue:
- AI analysis depends on `HEDERA_SHIELD_ANTHROPIC_API_KEY` and model settings.

Impact:
- Contextual AI scoring/explanations may be unavailable.

Workaround:
- Continue with rules-based compliance path.
- Preflight marks missing AI config as `YELLOW` rather than `RED` to allow integration progress.
