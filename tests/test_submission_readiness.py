from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "submission-readiness.sh"


REQUIRED_FILES = [
    "README.md",
    "SUBMISSION.md",
    "docs/TESTNET_SETUP.md",
    "docs/TESTNET_EVIDENCE.md",
    "docs/DEPLOY_PROOF.md",
    "docs/DEMO_RECORDING_RUNBOOK.md",
    "docs/FINAL_SUBMISSION_CHECKLIST.md",
    "artifacts/demo/3min-offline/harness/report.md",
    "artifacts/demo/3min-offline/harness/report.json",
    "artifacts/demo/3min-offline/harness/harness.log",
    "artifacts/demo/3min-offline/harness/smoke.log",
    "artifacts/demo/3min-offline/harness/validator.log",
    "artifacts/demo/3min-offline/submission-bundle.zip.sha256",
    "dist/submission-bundle.zip",
    "dist/release-evidence-20260310T000000Z.tar.gz",
    "artifacts/integration/release-20260310T000000Z/release-report.md",
    "artifacts/integration/release-20260310T000000Z/release-report.json",
]


def _write(path: Path, content: str = "ok\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_submission_readiness_passes_with_required_artifacts(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    script_path = project / "scripts" / "submission-readiness.sh"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SCRIPT, script_path)

    for rel in REQUIRED_FILES:
        _write(project / rel)

    report_path = project / "dist" / "readiness.txt"
    result = subprocess.run(
        ["bash", str(script_path), "--report-file", str(report_path)],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "READINESS|summary|PASS|submission readiness checks passed" in result.stdout
    report = report_path.read_text(encoding="utf-8")
    assert "Overall: PASS" in report


def test_submission_readiness_fails_with_missing_required_artifacts(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    script_path = project / "scripts" / "submission-readiness.sh"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SCRIPT, script_path)

    _write(project / "README.md")

    report_path = project / "dist" / "readiness.txt"
    result = subprocess.run(
        ["bash", str(script_path), "--report-file", str(report_path)],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "READINESS|doc_submission|FAIL|" in result.stdout
    assert "READINESS|summary|FAIL|submission readiness checks failed" in result.stdout

    report = report_path.read_text(encoding="utf-8")
    assert "Overall: FAIL" in report
