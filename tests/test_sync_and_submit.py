from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "sync-and-submit.sh"


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


def test_sync_script_reports_pending_commits_when_remote_unreachable(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    script_path = repo / "scripts" / "sync-and-submit.sh"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SCRIPT, script_path)
    _init_repo_with_commit(repo)
    _git(repo, "remote", "add", "origin", "https://nonexistent.invalid/hedera-shield.git")

    report_path = repo / "dist" / "sync-report.txt"
    push_status_path = repo / "PUSH_STATUS.md"
    result = _run(
        [
            "bash",
            str(script_path),
            "--report-file",
            str(report_path),
            "--max-retries",
            "2",
            "--initial-backoff-seconds",
            "0",
        ],
        cwd=repo,
    )

    assert result.returncode == 1
    assert "SYNC|remote_reachability|FAIL|" in result.stdout
    assert "SYNC|summary|FAIL|" in result.stdout
    assert report_path.exists()

    report = report_path.read_text(encoding="utf-8")
    assert "Push status: SKIPPED_UNREACHABLE" in report
    assert "Pending local commits: 1" in report
    assert "initial commit" in report
    assert "REMOTE_REACHABILITY_ERROR:" in report

    assert push_status_path.exists()
    push_status = push_status_path.read_text(encoding="utf-8")
    assert "# Push Failure Status" in push_status
    assert "Push status: SKIPPED_UNREACHABLE" in push_status
    assert "nonexistent.invalid" in push_status


def test_sync_script_retries_push_and_captures_final_error(tmp_path: Path) -> None:
    remote = tmp_path / "remote"
    remote.mkdir()
    _init_repo_with_commit(remote, file_name="seed.txt", content="seed\n")

    local = tmp_path / "local"
    clone = _run(["git", "clone", str(remote), str(local)], cwd=tmp_path)
    assert clone.returncode == 0

    _git(local, "config", "user.email", "test@example.com")
    _git(local, "config", "user.name", "Test User")
    script_path = local / "scripts" / "sync-and-submit.sh"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SCRIPT, script_path)
    (local / "change.txt").write_text("change\n", encoding="utf-8")
    _git(local, "add", "change.txt")
    _git(local, "commit", "-m", "local change")

    report_path = local / "dist" / "sync-report.txt"
    push_status_path = local / "PUSH_STATUS.md"
    result = _run(
        [
            "bash",
            str(script_path),
            "--report-file",
            str(report_path),
            "--max-retries",
            "2",
            "--initial-backoff-seconds",
            "0",
            "--max-backoff-seconds",
            "1",
        ],
        cwd=local,
    )

    assert result.returncode == 1
    assert "SYNC|remote_reachability|PASS|" in result.stdout
    assert "SYNC|push|FAIL|push failed after 2 attempts" in result.stdout

    report = report_path.read_text(encoding="utf-8")
    assert "Push status: FAILED_AFTER_RETRIES" in report
    assert "PUSH_ATTEMPTS:" in report
    assert "Attempt 1/2 exit=" in report
    assert "Attempt 2/2 exit=" in report
    assert "PUSH_FINAL_ERROR:" in report

    assert push_status_path.exists()
    push_status = push_status_path.read_text(encoding="utf-8")
    assert "Push status: FAILED_AFTER_RETRIES" in push_status
    assert "refusing to update checked out branch" in push_status
