from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GEN_SCRIPT = ROOT / "scripts" / "generate-portal-submission-packet.py"
VERIFY_SCRIPT = ROOT / "scripts" / "verify-portal-submission-packet.py"


def _write(path: Path, content: str = "ok\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _seed_min_project(project: Path) -> None:
    _write(project / "SUBMISSION.md", "## Hedera-Specific Integrations\nHTS and HCS\n")
    _write(
        project / "docs" / "SUBMISSION_FORM_DRAFT_PACK.md",
        "\n".join(
            [
                "## Problem Statement",
                "Problem",
                "",
                "## Solution Summary",
                "Solution",
                "",
                "## Architecture (Short Form)",
                "Architecture",
                "",
                "## Innovation / Differentiation",
                "Innovation",
                "",
                "## Setup and Run Steps (Judge-Friendly)",
                "```bash",
                "./scripts/release-evidence.sh",
                "```",
            ]
        )
        + "\n",
    )
    _write(
        project / "docs" / "DEMO_RECORDING_RUNBOOK.md",
        "\n".join(
            [
                "## 3-Minute Script (Offline-Safe Default)",
                "### 0:00-0:20 Setup",
                "```bash",
                "export DEMO_ID=\"3min-offline\"",
                "```",
                "### 0:20-1:20 Run harness",
                "```bash",
                "./scripts/run-integration-harness.sh --mode mock",
                "```",
            ]
        )
        + "\n",
    )

    _write(project / "README.md")
    _write(project / "docs" / "DEMO_NARRATION_3MIN.md")
    _write(project / "docs" / "FINAL_SUBMISSION_CHECKLIST.md")
    _write(project / "docs" / "TESTNET_SETUP.md")
    _write(project / "docs" / "TESTNET_EVIDENCE.md")
    _write(project / "docs" / "DEPLOY_PROOF.md")
    _write(project / "artifacts" / "demo" / "3min-offline" / "harness" / "report.md")
    _write(project / "artifacts" / "demo" / "3min-offline" / "harness" / "report.json", "{}\n")
    _write(project / "dist" / "submission-bundle.zip", "zip\n")
    _write(project / "dist" / "release-evidence-20260310T000000Z.tar.gz", "tgz\n")


def test_generate_portal_submission_packet_outputs_markdown_and_json(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    gen_script = project / "scripts" / "generate-portal-submission-packet.py"
    gen_script.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(GEN_SCRIPT, gen_script)

    _seed_min_project(project)

    timestamp = "20260310T120000Z"
    result = subprocess.run(
        ["python3", str(gen_script), "--timestamp", timestamp],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "PORTAL_PACKET|json|PASS|" in result.stdout

    json_path = project / "dist" / "portal-submission" / timestamp / "portal-submission-packet.json"
    md_path = project / "dist" / "portal-submission" / timestamp / "portal-submission-packet.md"
    assert json_path.exists()
    assert md_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["fields"]["title"] == "HederaShield: Hedera-Native AI Compliance Agent"
    assert payload["links"]["demo_video_url"] == "TODO_ADD_DEMO_VIDEO_URL"
    assert payload["links"]["deployed_url"] == "TODO_ADD_FINAL_DEPLOYED_URL_OR_NA"


def test_verify_portal_submission_packet_passes_then_fails_on_missing_path(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    gen_script = project / "scripts" / "generate-portal-submission-packet.py"
    verify_script = project / "scripts" / "verify-portal-submission-packet.py"
    gen_script.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(GEN_SCRIPT, gen_script)
    shutil.copyfile(VERIFY_SCRIPT, verify_script)

    _seed_min_project(project)

    timestamp = "20260310T130000Z"
    gen = subprocess.run(
        ["python3", str(gen_script), "--timestamp", timestamp],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )
    assert gen.returncode == 0

    verify = subprocess.run(
        ["python3", str(verify_script)],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )
    assert verify.returncode == 0
    assert "PORTAL_VERIFY|summary|PASS|portal submission packet is ready" in verify.stdout

    (project / "docs" / "DEPLOY_PROOF.md").unlink()
    verify_fail = subprocess.run(
        ["python3", str(verify_script)],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )
    assert verify_fail.returncode == 1
    assert "PORTAL_VERIFY|summary|FAIL|portal submission packet is not ready" in verify_fail.stdout
