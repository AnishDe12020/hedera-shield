from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
FREEZE_SCRIPT = ROOT / "scripts" / "submission-freeze.py"
VERIFY_SCRIPT = ROOT / "scripts" / "verify-submission-freeze.py"


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


def _write(path: Path, content: str = "ok\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _init_repo(project: Path) -> None:
    _run(["git", "init"], cwd=project)
    _run(["git", "config", "user.name", "Test User"], cwd=project)
    _run(["git", "config", "user.email", "test@example.com"], cwd=project)
    _write(project / "README.md", "test repo\n")
    _run(["git", "add", "README.md"], cwd=project)
    _run(["git", "commit", "-m", "init"], cwd=project)


def _copy_scripts(project: Path) -> None:
    scripts_dir = project / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FREEZE_SCRIPT, scripts_dir / "submission-freeze.py")
    shutil.copyfile(VERIFY_SCRIPT, scripts_dir / "verify-submission-freeze.py")


def test_submission_freeze_writes_timestamped_and_latest_manifests(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    _copy_scripts(project)
    _init_repo(project)

    _write(project / "dist" / "submission-bundle.zip", "bundle-v1\n")
    _write(project / "dist" / "submission-readiness-latest.txt", "ready\n")

    freeze_result = _run(["python3", "scripts/submission-freeze.py"], cwd=project)
    assert freeze_result.returncode == 0
    assert "FREEZE|manifest_latest_json|PASS" in freeze_result.stdout

    latest_json = project / "dist" / "submission-freeze" / "submission-freeze-latest.json"
    latest_md = project / "dist" / "submission-freeze" / "submission-freeze-latest.md"
    assert latest_json.exists()
    assert latest_md.exists()

    payload = json.loads(latest_json.read_text(encoding="utf-8"))
    assert payload["manifest_type"] == "submission_freeze"
    assert payload["repo"]["branch"] in {"master", "main"}
    assert len(payload["repo"]["commit_sha"]) == 40

    verify_result = _run(["python3", "scripts/verify-submission-freeze.py"], cwd=project)
    assert verify_result.returncode == 0
    assert "DRIFT|summary|PASS|no drift detected against freeze manifest" in verify_result.stdout


def test_submission_freeze_drift_detects_checksum_change(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    _copy_scripts(project)
    _init_repo(project)

    artifact = project / "dist" / "submission-bundle.zip"
    _write(artifact, "bundle-v1\n")

    freeze_result = _run(["python3", "scripts/submission-freeze.py"], cwd=project)
    assert freeze_result.returncode == 0

    _write(artifact, "bundle-v2\n")

    verify_result = _run(["python3", "scripts/verify-submission-freeze.py"], cwd=project)
    assert verify_result.returncode == 1
    assert "DRIFT|dist_submission_bundle_zip|DRIFT|checksum changed" in verify_result.stdout
    assert "DRIFT|summary|DRIFT|detected" in verify_result.stdout

    drift_latest = project / "dist" / "submission-freeze" / "drift-verify-latest.json"
    payload = json.loads(drift_latest.read_text(encoding="utf-8"))
    assert payload["summary"]["drift_count"] >= 1
