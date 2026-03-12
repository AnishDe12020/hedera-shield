# VALIDATION

Validation run timestamp (UTC): `2026-03-12T03:33:10Z`
Validation commit base: `14dbad9`

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
collected 108 items
...
======================== 102 passed, 6 skipped in 2.17s ========================
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
- `dist/submission-bundle.zip` (`77K`)
- SHA-256: `bc342dfa7254445bc927ad28b1be9dd3b36c1101f58523eb9593d6a20d327729`

## Credential Requirements

- No Hedera testnet operator credentials were required for the lint, test, and package commands above.
- Commands that require real testnet operator credentials are marked explicitly in `SUBMISSION.md`.
