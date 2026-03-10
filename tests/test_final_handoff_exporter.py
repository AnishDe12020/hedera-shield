from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
EXPORTER = ROOT / "scripts" / "final_handoff_exporter.py"
WRAPPER = ROOT / "scripts" / "final-handoff-export.sh"


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "checkout", "-b", "main"], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True, capture_output=True, text=True)
    _write(path / "README.md", "# repo\n")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True, text=True)


def _setup_runner_repo(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    (project / "scripts").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(EXPORTER, project / "scripts" / "final_handoff_exporter.py")
    shutil.copyfile(WRAPPER, project / "scripts" / "final-handoff-export.sh")
    (project / "scripts" / "final_handoff_exporter.py").chmod(0o755)
    (project / "scripts" / "final-handoff-export.sh").chmod(0o755)
    return project


def test_final_handoff_exporter_builds_master_indexes_and_copies_latest_artifacts(tmp_path: Path) -> None:
    project = _setup_runner_repo(tmp_path)

    repo_a = tmp_path / "gitlab-codeguard"
    repo_b = tmp_path / "hedera-shield"
    repo_c = tmp_path / "do-gradient-guard"
    repo_a.mkdir(parents=True, exist_ok=True)
    repo_b.mkdir(parents=True, exist_ok=True)
    repo_c.mkdir(parents=True, exist_ok=True)

    _init_git_repo(repo_a)
    _init_git_repo(repo_b)
    _init_git_repo(repo_c)

    _write(repo_a / "artifacts" / "submission-freeze" / "submission-freeze-latest.json", "{}\n")
    _write(repo_a / "artifacts" / "submission-freeze" / "submission-freeze-latest.md", "# freeze\n")
    _write(repo_a / "artifacts" / "handoff-index" / "handoff-index-latest.json", "{}\n")
    _write(repo_a / "artifacts" / "handoff-index" / "handoff-index-latest.md", "# handoff\n")
    _write(repo_a / "artifacts" / "submission-status" / "sync-submit-status.txt", "sync ok\n")
    _write(repo_a / "artifacts" / "submission-status" / "network-recovery-push-status-latest.json", "{}\n")
    _write(repo_a / "artifacts" / "submission-status" / "network-recovery-push-status-latest.txt", "push ok\n")
    _write(repo_a / "submission-bundle.zip", "bundle\n")

    _write(repo_b / "dist" / "submission-freeze" / "submission-freeze-latest.json", "{}\n")
    _write(repo_b / "dist" / "submission-freeze" / "submission-freeze-latest.md", "# freeze\n")
    _write(repo_b / "artifacts" / "handoff-index" / "20260310T170500Z" / "handoff-index.json", "{}\n")
    _write(repo_b / "artifacts" / "handoff-index" / "20260310T170500Z" / "handoff-index.md", "# handoff\n")
    _write(repo_b / "dist" / "sync-submit-status-latest.txt", "sync status\n")
    _write(repo_b / "dist" / "network-recovery-push-status-latest.json", "{}\n")
    _write(repo_b / "dist" / "network-recovery-push-status-latest.txt", "network status\n")
    _write(repo_b / "dist" / "submission-bundle.zip", "bundle\n")

    _write(repo_c / "docs" / "evidence" / "submission-freeze" / "submission-freeze-latest.json", "{}\n")
    _write(repo_c / "docs" / "evidence" / "submission-freeze" / "submission-freeze-latest.md", "# freeze\n")
    _write(repo_c / "artifacts" / "handoff-index" / "20260310T160500Z" / "handoff-index.json", "{}\n")
    _write(repo_c / "artifacts" / "handoff-index" / "20260310T160500Z" / "HANDOFF_INDEX.md", "# handoff\n")
    _write(repo_c / "docs" / "evidence" / "sync-submit-status-20260310T161250Z.md", "sync pending\n")
    _write(repo_c / "docs" / "evidence" / "submission-freeze" / "push-status-latest.json", "{}\n")
    _write(repo_c / "docs" / "evidence" / "submission-freeze" / "push-status-latest.md", "push fail\n")

    timestamp = "20260310T200000Z"
    result = _run(
        [
            "./scripts/final-handoff-export.sh",
            "--timestamp",
            timestamp,
            "--repo",
            f"gitlab-codeguard={repo_a}",
            "--repo",
            f"hedera-shield={repo_b}",
            "--repo",
            f"do-gradient-guard={repo_c}",
        ],
        cwd=project,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "FINAL_HANDOFF|summary|" in result.stdout

    package_dir = project / "dist" / "final-handoff" / f"final-handoff-{timestamp}"
    json_path = package_dir / "master-index.json"
    md_path = package_dir / "master-index.md"
    latest_json = project / "dist" / "final-handoff" / "final-handoff-latest.json"
    latest_md = project / "dist" / "final-handoff" / "final-handoff-latest.md"

    assert json_path.exists()
    assert md_path.exists()
    assert latest_json.exists()
    assert latest_md.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["manifest_type"] == "cross_repo_final_handoff"
    assert payload["read_only_collection"] is True
    assert payload["summary"]["repos_total"] == 3

    repo_a_payload = next(item for item in payload["repos"] if item["name"] == "gitlab-codeguard")
    bundle = repo_a_payload["artifacts"]["submission_bundle"]
    assert bundle["exists"] is True
    assert bundle["source_abs_path"].startswith("/")
    assert bundle["copied_abs_path"].startswith("/")
    assert Path(bundle["copied_abs_path"]).exists()


def test_final_handoff_exporter_marks_missing_repo_and_missing_artifacts(tmp_path: Path) -> None:
    project = _setup_runner_repo(tmp_path)

    present_repo = tmp_path / "present"
    present_repo.mkdir(parents=True, exist_ok=True)
    _init_git_repo(present_repo)

    missing_repo = tmp_path / "missing"
    timestamp = "20260310T201500Z"
    result = _run(
        [
            "python3",
            "scripts/final_handoff_exporter.py",
            "--timestamp",
            timestamp,
            "--repo",
            f"present={present_repo}",
            "--repo",
            f"missing={missing_repo}",
        ],
        cwd=project,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "FINAL_HANDOFF|status|WARN|" in result.stdout

    json_path = project / "dist" / "final-handoff" / f"final-handoff-{timestamp}" / "master-index.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert payload["summary"]["artifacts_missing"] > 0

    missing_payload = next(item for item in payload["repos"] if item["name"] == "missing")
    assert missing_payload["exists"] is False
    assert missing_payload["is_git_repo"] is False
    assert missing_payload["artifacts"]["handoff_index_json"]["exists"] is False
