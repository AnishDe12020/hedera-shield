from __future__ import annotations

import shutil
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "package-submission.sh"


REQUIRED_ARCHIVE_ENTRIES = {
    "README.md",
    "SUBMISSION.md",
    "DEPLOY_STATUS.md",
    "docs/TESTNET_SETUP.md",
    "docs/TESTNET_EVIDENCE.md",
    "docs/DEPLOY_PROOF.md",
    "docs/DEMO_RECORDING_RUNBOOK.md",
    "docs/DEMO_NARRATION_3MIN.md",
    "docs/SUBMISSION_FORM_DRAFT_PACK.md",
    "docs/FINAL_SUBMISSION_CHECKLIST.md",
    ".env.testnet.example",
    "config/sprint-repos.json",
    "scripts/run-integration-harness.sh",
    "scripts/run-testnet-smoke.sh",
    "scripts/capture-testnet-evidence.sh",
    "scripts/generate-integration-evidence.py",
    "scripts/package-submission.sh",
    "scripts/release-evidence.sh",
    "scripts/generate-handoff-index.py",
    "scripts/final_handoff_exporter.py",
    "scripts/final-handoff-export.sh",
    "scripts/sprint-multi-repo-dashboard.py",
    "scripts/submission-readiness.sh",
    "scripts/pre-submit-verify.py",
    "scripts/submission-freeze.py",
    "scripts/verify-submission-freeze.py",
    "scripts/sync-and-submit.sh",
    "scripts/offline-handoff.sh",
}


def test_package_submission_creates_bundle_with_required_entries() -> None:
    bundle = ROOT / "dist" / "submission-bundle.zip"
    if bundle.exists():
        bundle.unlink()

    result = subprocess.run(
        [str(SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "PACKAGE|bundle|PASS|" in result.stdout
    assert bundle.exists()

    with zipfile.ZipFile(bundle, "r") as archive:
        names = set(archive.namelist())

    assert REQUIRED_ARCHIVE_ENTRIES.issubset(names)


def _write_file(path: Path, content: str = "placeholder\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_package_submission_fails_when_required_file_missing(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()

    script_path = project_root / "scripts" / "package-submission.sh"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SCRIPT, script_path)

    for entry in REQUIRED_ARCHIVE_ENTRIES - {"docs/DEPLOY_PROOF.md", "scripts/package-submission.sh"}:
        _write_file(project_root / entry)

    result = subprocess.run(
        ["bash", str(script_path)],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "PACKAGE|required_files|FAIL|" in result.stdout
    assert "docs/DEPLOY_PROOF.md" in result.stdout
