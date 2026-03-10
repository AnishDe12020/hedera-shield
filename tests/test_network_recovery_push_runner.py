from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "network-recovery-push-runner.sh"


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


def test_recovery_runner_reports_blocked_state_when_remote_unreachable(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    script_path = repo / "scripts" / "network-recovery-push-runner.sh"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SCRIPT, script_path)
    _init_repo_with_commit(repo)
    _git(repo, "remote", "add", "origin", "https://nonexistent.invalid/hedera-shield.git")

    report_path = repo / "dist" / "recovery-report.txt"
    json_path = repo / "dist" / "recovery-report.json"
    result = _run(
        [
            "bash",
            str(script_path),
            "--max-checks",
            "1",
            "--check-interval-seconds",
            "0",
            "--report-file",
            str(report_path),
            "--json-file",
            str(json_path),
        ],
        cwd=repo,
    )

    assert result.returncode == 1
    assert "RECOVERY|dns|FAIL|" in result.stdout
    assert "RECOVERY|remote_reachability|FAIL|" in result.stdout
    assert "RECOVERY|summary|FAIL|" in result.stdout
    assert report_path.exists()
    assert json_path.exists()

    report = report_path.read_text(encoding="utf-8")
    assert "Push status: BLOCKED_REMOTE_UNREACHABLE" in report
    assert "REMOTE_REACHABILITY_ERROR:" in report

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["blocked"] is True
    assert payload["push_status"] == "BLOCKED_REMOTE_UNREACHABLE"
    assert payload["errors"]["remote_reachability"]


def test_recovery_runner_dry_run_does_not_push(tmp_path: Path) -> None:
    remote = tmp_path / "remote"
    remote.mkdir()
    _init_repo_with_commit(remote, file_name="seed.txt", content="seed\n")

    local = tmp_path / "local"
    clone = _run(["git", "clone", str(remote), str(local)], cwd=tmp_path)
    assert clone.returncode == 0

    _git(local, "config", "user.email", "test@example.com")
    _git(local, "config", "user.name", "Test User")

    script_path = local / "scripts" / "network-recovery-push-runner.sh"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SCRIPT, script_path)

    (local / "change.txt").write_text("change\n", encoding="utf-8")
    _git(local, "add", "change.txt")
    _git(local, "commit", "-m", "local change")

    report_path = local / "dist" / "recovery-report.txt"
    json_path = local / "dist" / "recovery-report.json"
    result = _run(
        [
            "bash",
            str(script_path),
            "--max-checks",
            "1",
            "--check-interval-seconds",
            "0",
            "--dry-run",
            "--dns-host",
            "localhost",
            "--report-file",
            str(report_path),
            "--json-file",
            str(json_path),
        ],
        cwd=local,
    )

    assert result.returncode == 0
    assert "RECOVERY|push|WARN|dry-run enabled; push not executed" in result.stdout

    branch = _git(local, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    head_remote = _git(local, "rev-parse", f"origin/{branch}").stdout.strip()
    head_local = _git(local, "rev-parse", "HEAD").stdout.strip()
    assert head_remote != head_local

    report = report_path.read_text(encoding="utf-8")
    assert "Push status: DRY_RUN_PENDING" in report

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["blocked"] is False
    assert payload["dry_run"] is True
    assert payload["push_status"] == "DRY_RUN_PENDING"


def test_recovery_runner_captures_exact_push_error(tmp_path: Path) -> None:
    remote = tmp_path / "remote"
    remote.mkdir()
    _init_repo_with_commit(remote, file_name="seed.txt", content="seed\n")

    local = tmp_path / "local"
    clone = _run(["git", "clone", str(remote), str(local)], cwd=tmp_path)
    assert clone.returncode == 0

    _git(local, "config", "user.email", "test@example.com")
    _git(local, "config", "user.name", "Test User")

    script_path = local / "scripts" / "network-recovery-push-runner.sh"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SCRIPT, script_path)

    (local / "change.txt").write_text("change\n", encoding="utf-8")
    _git(local, "add", "change.txt")
    _git(local, "commit", "-m", "local change")

    report_path = local / "dist" / "recovery-report.txt"
    json_path = local / "dist" / "recovery-report.json"
    result = _run(
        [
            "bash",
            str(script_path),
            "--max-checks",
            "1",
            "--check-interval-seconds",
            "0",
            "--dns-host",
            "localhost",
            "--report-file",
            str(report_path),
            "--json-file",
            str(json_path),
        ],
        cwd=local,
    )

    assert result.returncode == 1
    assert "RECOVERY|push|FAIL|push failed" in result.stdout

    report = report_path.read_text(encoding="utf-8")
    assert "Push status: PUSH_FAILED" in report
    assert "PUSH_FINAL_ERROR:" in report
    assert "refusing to update checked out branch" in report

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["blocked"] is True
    assert payload["push_status"] == "PUSH_FAILED"
    assert "refusing to update checked out branch" in payload["errors"]["push"]
