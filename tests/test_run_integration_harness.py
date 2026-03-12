from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "run-integration-harness.sh"


def _write_valid_placeholder_env(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "HEDERA_SHIELD_HEDERA_NETWORK=testnet",
                "HEDERA_SHIELD_HEDERA_OPERATOR_ID=0.0.YOUR_OPERATOR_ACCOUNT_ID",
                "HEDERA_SHIELD_HEDERA_OPERATOR_KEY=YOUR_ED25519_PRIVATE_KEY",
                "HEDERA_SHIELD_MIRROR_NODE_URL=https://testnet.mirrornode.hedera.com",
                "HEDERA_SHIELD_MIRROR_NODE_POLL_INTERVAL=10",
                "HEDERA_SHIELD_ANTHROPIC_API_KEY=YOUR_ANTHROPIC_API_KEY_OR_EMPTY",
                "HEDERA_SHIELD_AI_MODEL=claude-sonnet-4-20250514",
                "HEDERA_SHIELD_LARGE_TRANSFER_THRESHOLD=10000",
                "HEDERA_SHIELD_VELOCITY_WINDOW_SECONDS=3600",
                "HEDERA_SHIELD_VELOCITY_MAX_TRANSFERS=50",
                "HEDERA_SHIELD_API_HOST=0.0.0.0",
                "HEDERA_SHIELD_API_PORT=8000",
                'HEDERA_SHIELD_MONITORED_TOKEN_IDS=["0.0.YOUR_TOKEN_ID"]',
                'HEDERA_SHIELD_SANCTIONED_ADDRESSES=["0.0.YOUR_SANCTIONED_ACCOUNT_ID"]',
            ]
        ),
        encoding="utf-8",
    )


def _run_harness(args: list[str], extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def test_mock_mode_succeeds_and_writes_artifacts(tmp_path: Path) -> None:
    env_file = tmp_path / ".env.testnet"
    artifacts_dir = tmp_path / "artifacts"
    _write_valid_placeholder_env(env_file)

    result = _run_harness(["--mode", "mock", "--env-file", str(env_file), "--artifacts-dir", str(artifacts_dir)])

    assert result.returncode == 0
    assert "HARNESS|summary|PASS|harness checks passed" in result.stdout
    assert (artifacts_dir / "report.md").exists()
    assert (artifacts_dir / "report.json").exists()
    assert (artifacts_dir / "validator.log").exists()
    assert (artifacts_dir / "smoke.log").exists()
    assert (artifacts_dir / "integration.log").exists()


def test_real_mode_requires_explicit_opt_in(tmp_path: Path) -> None:
    env_file = tmp_path / ".env.testnet"
    artifacts_dir = tmp_path / "artifacts"
    _write_valid_placeholder_env(env_file)

    result = _run_harness(["--mode", "real", "--env-file", str(env_file), "--artifacts-dir", str(artifacts_dir)])

    assert result.returncode == 0
    assert "HARNESS|real_fallback|PASS|requested real mode but using deterministic dry-run fallback:" in result.stdout
    assert "missing HEDERA_SHIELD_ENABLE_REAL_TESTNET=1" in result.stdout
    assert "HARNESS|integration_pytest|SKIP|skipped: deterministic dry-run fallback mode" in result.stdout
    assert "HARNESS|summary|PASS|harness checks passed" in result.stdout

    report = json.loads((artifacts_dir / "report.json").read_text(encoding="utf-8"))
    assert report["mode"] == "real"
    assert report["effective_mode"] == "mock"
    assert report["dry_run_fallback"] is True
    assert report["checks"]["harness"]["status"] == "PASS"


def test_real_mode_rejects_placeholder_credentials_even_with_opt_in(tmp_path: Path) -> None:
    env_file = tmp_path / ".env.testnet"
    artifacts_dir = tmp_path / "artifacts"
    _write_valid_placeholder_env(env_file)

    result = _run_harness(
        ["--mode", "real", "--env-file", str(env_file), "--artifacts-dir", str(artifacts_dir)],
        extra_env={"HEDERA_SHIELD_ENABLE_REAL_TESTNET": "1"},
    )

    assert result.returncode == 0
    assert "HARNESS|real_fallback|PASS|requested real mode but using deterministic dry-run fallback:" in result.stdout
    assert "operator id/key are placeholders" in result.stdout
    assert "HARNESS|integration_pytest|SKIP|skipped: deterministic dry-run fallback mode" in result.stdout

    report = json.loads((artifacts_dir / "report.json").read_text(encoding="utf-8"))
    assert report["mode"] == "real"
    assert report["effective_mode"] == "mock"
    assert report["dry_run_fallback"] is True
