from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "testnet-preflight.sh"


def test_testnet_preflight_help() -> None:
    result = subprocess.run(
        [str(SCRIPT), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert "testnet-preflight.sh" in result.stdout


def test_testnet_preflight_fails_when_env_file_missing(tmp_path: Path) -> None:
    missing_env = tmp_path / ".env.missing"
    result = subprocess.run(
        [str(SCRIPT), "--env-file", str(missing_env), "--timeout-seconds", "1"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "OVERALL READINESS: RED" in result.stdout
    assert "PREFLIGHT|summary|FAIL|integration preflight gate failed" in result.stdout
