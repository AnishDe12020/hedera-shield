from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "pre-submit-verify.py"


REQUIRED_FILES = [
    "README.md",
    "SUBMISSION.md",
    "docs/SUBMISSION_FORM_DRAFT_PACK.md",
    "docs/DEMO_RECORDING_RUNBOOK.md",
    "docs/DEMO_NARRATION_3MIN.md",
    "docs/FINAL_SUBMISSION_CHECKLIST.md",
    "docs/TESTNET_SETUP.md",
    "docs/TESTNET_EVIDENCE.md",
    "docs/DEPLOY_PROOF.md",
    "dist/submission-bundle.zip",
    "dist/submission-readiness-latest.txt",
    "artifacts/demo/3min-offline/harness/report.md",
    "artifacts/demo/3min-offline/harness/report.json",
    "artifacts/demo/3min-offline/harness/harness.log",
    "artifacts/demo/3min-offline/harness/smoke.log",
    "artifacts/demo/3min-offline/harness/validator.log",
    "artifacts/demo/3min-offline/submission-bundle.zip.sha256",
    "dist/release-evidence-20260310T000000Z.tar.gz",
]


def _write(path: Path, content: str = "ok\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_pre_submit_verify_passes_with_required_inputs(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    script_path = project / "scripts" / "pre-submit-verify.py"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SCRIPT, script_path)

    for rel in REQUIRED_FILES:
        _write(project / rel)

    report_path = project / "dist" / "verify.txt"
    result = subprocess.run(
        ["python3", str(script_path), "--report-file", str(report_path)],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "VERIFY|summary|PASS|pre-submit verification checks passed" in result.stdout

    report = report_path.read_text(encoding="utf-8")
    assert "Overall: PASS" in report
    latest = (project / "dist" / "pre-submit-verify-latest.txt").read_text(encoding="utf-8")
    assert "Overall: PASS" in latest


def test_pre_submit_verify_fails_when_required_input_missing(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    script_path = project / "scripts" / "pre-submit-verify.py"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SCRIPT, script_path)

    for rel in REQUIRED_FILES:
        if rel == "docs/DEMO_NARRATION_3MIN.md":
            continue
        _write(project / rel)

    report_path = project / "dist" / "verify.txt"
    result = subprocess.run(
        ["python3", str(script_path), "--report-file", str(report_path)],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "VERIFY|docs_DEMO_NARRATION_3MIN.md|FAIL|missing docs/DEMO_NARRATION_3MIN.md" in result.stdout
    assert "VERIFY|summary|FAIL|pre-submit verification checks failed" in result.stdout

    report = report_path.read_text(encoding="utf-8")
    assert "Overall: FAIL" in report
