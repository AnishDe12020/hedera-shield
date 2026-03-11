## 2026-03-11 Validation Snapshot

- Full test suite (`pytest`): **100 passed, 6 skipped** (`106` collected, `2.19s`)
- Targeted network recovery test file (`pytest -q tests/test_network_recovery_push_runner.py`): **3 passed**
- DNS/remote-unreachable recovery test path is now deterministic via explicit `--dns-host nonexistent.invalid`
