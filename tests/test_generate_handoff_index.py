from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "generate-handoff-index.py"


def _write(path: Path, content: str = "ok\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_handoff_index_generates_markdown_and_json_with_key_links(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    script_path = project / "scripts" / "generate-handoff-index.py"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SCRIPT, script_path)

    _write(project / "dist" / "release-evidence-20260310T120000Z.tar.gz", "bundle")
    _write(project / "artifacts" / "integration" / "release-20260310T120000Z" / "release-report.md")
    _write(project / "artifacts" / "integration" / "release-20260310T120000Z" / "release-report.json", "{}\n")
    _write(project / "artifacts" / "integration" / "release-20260310T120000Z" / "mock" / "report.md")
    _write(project / "artifacts" / "integration" / "release-20260310T120000Z" / "mock" / "report.json", "{}\n")
    _write(project / "artifacts" / "offline-handoff" / "20260310T130000Z" / "handoff-summary.txt")
    _write(project / "artifacts" / "offline-handoff" / "20260310T130000Z" / "offline.bundle", "bundle")
    _write(project / "artifacts" / "offline-handoff" / "20260310T130000Z" / "RESTORE_APPLY.md")
    _write(project / "docs" / "DEMO_RECORDING_RUNBOOK.md")
    _write(project / "docs" / "FINAL_SUBMISSION_CHECKLIST.md")
    _write(project / "dist" / "submission-readiness-latest.txt")
    _write(project / "dist" / "sync-submit-status-latest.txt")

    timestamp = "20260310T150000Z"
    result = subprocess.run(
        ["python3", str(script_path), "--timestamp", timestamp],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "HANDOFF_INDEX|summary|" in result.stdout

    out_dir = project / "artifacts" / "handoff-index" / timestamp
    md_path = out_dir / "handoff-index.md"
    json_path = out_dir / "handoff-index.json"

    assert md_path.exists()
    assert json_path.exists()

    report = json.loads(json_path.read_text(encoding="utf-8"))
    assert report["summary"]["fail"] == 0
    assert report["latest_paths"]["release_bundle_latest"].endswith("release-evidence-20260310T120000Z.tar.gz")
    assert report["latest_paths"]["offline_handoff_dir_latest"].endswith("20260310T130000Z")

    markdown = md_path.read_text(encoding="utf-8")
    assert "docs/DEMO_RECORDING_RUNBOOK.md" in markdown
    assert "docs/FINAL_SUBMISSION_CHECKLIST.md" in markdown


def test_handoff_index_handles_missing_optional_artifacts_and_includes_push_errors(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    script_path = project / "scripts" / "generate-handoff-index.py"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SCRIPT, script_path)

    _write(project / "docs" / "DEMO_RECORDING_RUNBOOK.md")
    _write(project / "docs" / "FINAL_SUBMISSION_CHECKLIST.md")
    _write(
        project / "dist" / "sync-submit-status-latest.txt",
        "REMOTE_REACHABILITY_ERROR:\n"
        "fatal: unable to access 'https://example.invalid/repo.git/': Could not resolve host\n"
        "\n"
        "PUSH_FINAL_ERROR:\n"
        "fatal: unable to access 'https://example.invalid/repo.git/': Could not resolve host\n"
        "\n",
    )

    timestamp = "20260310T160000Z"
    result = subprocess.run(
        ["python3", str(script_path), "--timestamp", timestamp],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "HANDOFF_INDEX|summary|ACTION_NEEDED|" in result.stdout

    json_path = project / "artifacts" / "handoff-index" / timestamp / "handoff-index.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert payload["summary"]["warn"] > 0
    assert "sync_context" in payload
    assert "Could not resolve host" in payload["sync_context"]["push_final_error"]

    by_key = {item["key"]: item for item in payload["items"]}
    assert by_key["release_bundle_latest"]["status"] == "WARN"
    assert by_key["demo_runbook"]["status"] == "PASS"
    assert by_key["final_submission_checklist"]["status"] == "PASS"
