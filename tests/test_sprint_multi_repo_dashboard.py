from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "sprint-multi-repo-dashboard.py"
SYNC_HELPER = ROOT / "scripts" / "sync-and-submit.sh"


def _run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    run_env = dict(os.environ)
    run_env.setdefault("GIT_TERMINAL_PROMPT", "0")
    if env:
        run_env.update(env)
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False, env=run_env)


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return _run(["git", *args], cwd=cwd)


def _init_repo_with_commit(path: Path, file_name: str = "README.md", content: str = "hello\n") -> None:
    _git(path, "init")
    _git(path, "config", "user.email", "test@example.com")
    _git(path, "config", "user.name", "Test User")
    (path / file_name).write_text(content, encoding="utf-8")
    _git(path, "add", file_name)
    _git(path, "commit", "-m", "initial commit")


def test_dashboard_generates_timestamped_and_latest_outputs(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    script_path = project / "scripts" / "sprint-multi-repo-dashboard.py"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SCRIPT, script_path)

    repo = project / "repo-a"
    repo.mkdir()
    _init_repo_with_commit(repo)
    _git(repo, "remote", "add", "origin", "https://nonexistent.invalid/hedera-shield.git")
    (repo / "dist").mkdir(parents=True, exist_ok=True)
    (repo / "dist" / "sync-submit-status-latest.txt").write_text("sync report\n", encoding="utf-8")

    config = project / "repo-config.json"
    config.write_text(
        json.dumps({"repos": [{"name": "gitlab", "path": "repo-a", "remote": "origin"}]}, indent=2) + "\n",
        encoding="utf-8",
    )

    timestamp = "20260310T180000Z"
    result = _run(
        [
            "python3",
            str(script_path),
            "--repo-config",
            str(config),
            "--timestamp",
            timestamp,
        ],
        cwd=project,
    )

    assert result.returncode == 0
    assert "SPRINT_DASH|summary|WARN|" in result.stdout

    out_dir = project / "dist" / "sprint-status"
    md_path = out_dir / f"sprint-dashboard-{timestamp}.md"
    json_path = out_dir / f"sprint-dashboard-{timestamp}.json"
    latest_md = out_dir / "sprint-dashboard-latest.md"
    latest_json = out_dir / "sprint-dashboard-latest.json"

    assert md_path.exists()
    assert json_path.exists()
    assert latest_md.exists()
    assert latest_json.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["summary"]["warn"] == 1
    assert payload["repos"][0]["remote_reachability"]["status"] == "FAIL"
    assert "nonexistent.invalid" in payload["repos"][0]["remote_reachability"]["error"]
    assert payload["repos"][0]["latest_status_artifacts"]["sync_submit_latest"] == "dist/sync-submit-status-latest.txt"


def test_dashboard_attempt_push_captures_exact_error(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    local = project / "local"
    remote = project / "remote"
    remote.mkdir()
    _init_repo_with_commit(remote, "seed.txt", "seed\n")

    clone = _run(["git", "clone", str(remote), str(local)], cwd=project)
    assert clone.returncode == 0
    _git(local, "config", "user.email", "test@example.com")
    _git(local, "config", "user.name", "Test User")

    (local / "scripts").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SCRIPT, local / "scripts" / "sprint-multi-repo-dashboard.py")
    shutil.copyfile(SYNC_HELPER, local / "scripts" / "sync-and-submit.sh")

    (local / "change.txt").write_text("change\n", encoding="utf-8")
    _git(local, "add", "change.txt")
    _git(local, "commit", "-m", "local change")

    timestamp = "20260310T181000Z"
    result = _run(
        [
            "python3",
            str(local / "scripts" / "sprint-multi-repo-dashboard.py"),
            "--repo",
            "hedera=.",
            "--attempt-push",
            "--timestamp",
            timestamp,
        ],
        cwd=local,
    )

    assert result.returncode == 1
    assert "SPRINT_DASH|summary|FAIL|" in result.stdout

    json_path = local / "dist" / "sprint-status" / f"sprint-dashboard-{timestamp}.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    repo = payload["repos"][0]

    assert repo["remote_reachability"]["status"] == "PASS"
    assert repo["attempt_push"]["status"] == "FAIL"
    assert repo["attempt_push"]["report_path"].startswith("dist/sprint-status/sync-submit-attempt-")
    assert "refusing to update checked out branch" in repo["attempt_push"]["error"]

