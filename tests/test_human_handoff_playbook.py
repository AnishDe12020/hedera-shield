from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "generate-human-handoff-playbook.py"


def _write(path: Path, content: str = "ok\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _seed_min_project(project: Path) -> None:
    _write(project / "docs" / "DEMO_RECORDING_RUNBOOK.md")
    _write(project / "docs" / "DEMO_NARRATION_3MIN.md")
    _write(project / "docs" / "SUBMISSION_FORM_DRAFT_PACK.md")
    _write(project / "docs" / "FINAL_SUBMISSION_CHECKLIST.md")
    _write(project / "artifacts" / "demo" / "3min-offline" / "harness" / "report.md")
    _write(project / "artifacts" / "demo" / "3min-offline" / "harness" / "report.json", "{}\n")
    _write(project / "artifacts" / "demo" / "3min-offline" / "submission-bundle.zip.sha256", "abc  dist/submission-bundle.zip\n")
    _write(project / "dist" / "submission-bundle.zip", "zip\n")
    _write(project / "dist" / "submission-readiness-latest.txt")
    _write(project / "dist" / "pre-submit-verify-latest.txt")
    _write(project / "dist" / "portal-submission" / "portal-submission-packet-latest.md")
    _write(
        project / "dist" / "portal-submission" / "portal-submission-packet-latest.json",
        json.dumps(
            {
                "links": {
                    "repo_url": "git@github.com:AnishDe12020/hedera-shield.git",
                    "commit_sha": "abc123",
                    "demo_video_url": "TODO_ADD_DEMO_VIDEO_URL",
                }
            },
            indent=2,
        )
        + "\n",
    )


def test_playbook_outputs_timestamped_and_latest_and_marks_demo_url_blocker(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    script_path = project / "scripts" / "generate-human-handoff-playbook.py"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SCRIPT, script_path)

    _seed_min_project(project)

    timestamp = "20260310T220000Z"
    result = subprocess.run(
        ["python3", str(script_path), "--timestamp", timestamp],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "HANDOFF_PLAYBOOK|summary|BLOCKED|" in result.stdout

    json_path = project / "dist" / "handoff-playbook" / timestamp / "human-handoff-playbook.json"
    md_path = project / "dist" / "handoff-playbook" / timestamp / "human-handoff-playbook.md"
    latest_json = project / "dist" / "handoff-playbook" / "human-handoff-playbook-latest.json"
    latest_md = project / "dist" / "handoff-playbook" / "human-handoff-playbook-latest.md"

    assert json_path.exists()
    assert md_path.exists()
    assert latest_json.exists()
    assert latest_md.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["readiness"]["status"] == "BLOCKED"
    blocker_keys = {item["key"] for item in payload["blockers"]}
    assert "missing_demo_video_url" in blocker_keys

    markdown = md_path.read_text(encoding="utf-8")
    assert "Readiness Gate: **BLOCKED**" in markdown
    assert str((project / "docs" / "DEMO_RECORDING_RUNBOOK.md").resolve()) in markdown


def test_playbook_ready_when_urls_and_required_artifacts_present(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    script_path = project / "scripts" / "generate-human-handoff-playbook.py"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SCRIPT, script_path)

    _seed_min_project(project)

    timestamp = "20260310T220500Z"
    result = subprocess.run(
        [
            "python3",
            str(script_path),
            "--timestamp",
            timestamp,
            "--demo-video-url",
            "https://youtu.be/demo123",
            "--portal-submission-url",
            "https://portal.hedera.com/submissions/123",
        ],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "HANDOFF_PLAYBOOK|summary|READY|" in result.stdout

    json_path = project / "dist" / "handoff-playbook" / timestamp / "human-handoff-playbook.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["readiness"]["status"] == "READY"
    assert payload["readiness"]["open_blockers"] == 0
    assert payload["inputs"]["demo_video_url"] == "https://youtu.be/demo123"

    step_status = {item["key"]: item["status"] for item in payload["steps"]}
    assert step_status["record_demo"] == "DONE"
    assert step_status["final_submit"] == "PENDING"
