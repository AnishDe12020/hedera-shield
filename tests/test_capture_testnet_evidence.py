from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "capture-testnet-evidence.sh"


def _write_placeholder_env(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "HEDERA_SHIELD_HEDERA_NETWORK=testnet",
                "HEDERA_SHIELD_HEDERA_OPERATOR_ID=0.0.YOUR_OPERATOR_ACCOUNT_ID",
                "HEDERA_SHIELD_HEDERA_OPERATOR_KEY=YOUR_ED25519_PRIVATE_KEY",
                "HEDERA_SHIELD_MIRROR_NODE_URL=https://testnet.mirrornode.hedera.com",
            ]
        ),
        encoding="utf-8",
    )


def _run_capture(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_capture_script_uses_dry_run_when_credentials_are_placeholders(tmp_path: Path) -> None:
    env_file = tmp_path / ".env.testnet"
    output_file = tmp_path / "TESTNET_EVIDENCE.md"
    _write_placeholder_env(env_file)

    result = _run_capture(["--env-file", str(env_file), "--output", str(output_file)])

    assert result.returncode == 0
    assert "EVIDENCE|mode|DRY_RUN|placeholder operator credentials" in result.stdout
    assert "Dry-run commands to execute after credentials are ready:" in result.stdout
    assert (
        f"HEDERA_SHIELD_ENABLE_REAL_TESTNET=1 ./scripts/run-integration-harness.sh --mode real --env-file {env_file}"
        in result.stdout
    )
    assert (
        f"./scripts/capture-testnet-evidence.sh --env-file {env_file} --output {output_file} --limit 3"
        in result.stdout
    )
    assert output_file.exists()


def test_capture_script_writes_evidence_markdown_schema(tmp_path: Path) -> None:
    env_file = tmp_path / ".env.testnet"
    output_file = tmp_path / "TESTNET_EVIDENCE.md"
    _write_placeholder_env(env_file)
    tx_id = "0.0.12345@1700000000.000000000"

    result = _run_capture(
        [
            "--env-file",
            str(env_file),
            "--output",
            str(output_file),
            "--tx-id",
            tx_id,
        ]
    )

    assert result.returncode == 0
    content = output_file.read_text(encoding="utf-8")

    assert content.startswith("# HederaShield Testnet Evidence\n")
    assert re.search(r"- Generated \(UTC\): `[^`]+`", content)
    assert "- Capture mode: `DRY_RUN`" in content
    assert "## Captured Transactions" in content
    assert "| tx_id | tx_hash | mirror_link | hashscan_link |" in content
    assert f"| `{tx_id}` | `N/A (manual)` |" in content
    assert f"<https://testnet.mirrornode.hedera.com/api/v1/transactions/{tx_id}>" in content
    assert f"<https://hashscan.io/testnet/transaction/{tx_id}>" in content
    assert "## Reproduction Commands" in content
