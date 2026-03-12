# VALIDATION

Validation run timestamp (UTC): `2026-03-12T03:10:58Z`
Validation commit base: `1d599a7`

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
collected 106 items
...
======================== 100 passed, 6 skipped in 2.13s ========================
```

Notes:
- The 6 skipped tests are the live testnet integration tests gated behind `HEDERA_SHIELD_RUN_INTEGRATION=1`.

## 3) Build / Submission Package

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
- `dist/submission-bundle.zip` (`76K`)
- SHA-256: `88e4ac6ac2d395fd4801d73d11d62f3eceff4eabd8a32c2f6b3fb5e91c328d39`

## Credential Requirements

- No Hedera testnet operator credentials were required for the lint, test, and package commands above.
- Commands that require real testnet operator credentials are marked explicitly in `SUBMISSION.md`.
