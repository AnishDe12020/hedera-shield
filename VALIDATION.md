# VALIDATION

Validation run timestamp (UTC): `2026-03-12T03:45:16Z`
Validation commit base: `c7e563d`

## 1) Lint

Command:

```bash
ruff check hedera_shield/ tests/
```

Exact outcome:

```text
All checks passed!
```

## 2) Tests

Command:

```bash
venv/bin/pytest tests/ -v --tb=short
```

Exact outcome (summary):

```text
collecting ... collected 108 items
...
======================== 102 passed, 6 skipped in 2.14s ========================
```

Notes:
- The 6 skipped tests are live testnet integration tests gated behind `HEDERA_SHIELD_RUN_INTEGRATION=1`.

## 3) Readiness + Portal Checks

Commands:

```bash
./scripts/submission-readiness.sh
./scripts/pre-submit-verify.py
./scripts/generate-portal-submission-packet.py
./scripts/verify-portal-submission-packet.py
./scripts/sprint-multi-repo-dashboard.py
```

Exact outcome (summary):

```text
READINESS|summary|PASS|submission readiness checks passed
VERIFY|summary|PASS|pre-submit verification checks passed
PORTAL_PACKET|latest|PASS|updated dist/portal-submission/portal-submission-packet-latest.md
PORTAL_VERIFY|summary|PASS|portal submission packet is ready
SPRINT_DASH|summary|WARN|PASS=0 WARN=3 FAIL=0
```

Notes:
- Sprint dashboard warnings are remote reachability/DNS issues (`Could not resolve hostname github.com`), not local build/test failures.

## 4) Build / Submission Package

Command:

```bash
./scripts/package-submission.sh
```

Exact outcome:

```text
PACKAGE|required_files|PASS|all required files present
PACKAGE|bundle|PASS|created /home/anish/hedera-shield/dist/submission-bundle.zip with 39 files
```

Produced artifact:
- `dist/submission-bundle.zip`
- SHA-256: `f170914096ddd7064f6ad0c8d8e250ce53012ff32cd524f4401cce7602eefce1`

## Credential Requirements

- No Hedera testnet operator credentials were required for the commands above.
- Commands requiring real testnet operator credentials are explicitly marked in `SUBMISSION.md`.
