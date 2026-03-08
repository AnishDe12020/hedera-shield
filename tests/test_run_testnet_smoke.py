from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "run-testnet-smoke.sh"


def _write_valid_env(path: Path) -> None:
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


def _run_smoke(env_file: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["HEDERA_SHIELD_SMOKE_SKIP_NETWORK"] = "1"
    return subprocess.run(
        [str(SCRIPT), str(env_file)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def test_smoke_script_outputs_structured_lines_for_success(tmp_path: Path) -> None:
    env_file = tmp_path / ".env.testnet"
    _write_valid_env(env_file)

    result = _run_smoke(env_file)
    lines = [line for line in result.stdout.splitlines() if line.strip()]

    assert result.returncode == 0
    assert lines
    assert lines[-1] == "SMOKE|summary|PASS|all checks passed"

    pattern = re.compile(r"^SMOKE\|[a-z0-9_]+\|(PASS|FAIL)\|.+$")
    assert all(pattern.match(line) for line in lines)


def test_smoke_script_fails_when_required_env_is_missing(tmp_path: Path) -> None:
    env_file = tmp_path / ".env.testnet"
    _write_valid_env(env_file)

    text = env_file.read_text(encoding="utf-8")
    text = text.replace("HEDERA_SHIELD_API_PORT=8000\n", "")
    env_file.write_text(text, encoding="utf-8")

    result = _run_smoke(env_file)

    assert result.returncode == 1
    assert "SMOKE|env_validation|FAIL|" in result.stdout
    assert "Missing required variable: HEDERA_SHIELD_API_PORT" in result.stdout
    assert "SMOKE|summary|FAIL|" in result.stdout
