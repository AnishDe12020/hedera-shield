from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "offline-handoff.sh"


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return _run(["git", *args], cwd=cwd)


def _init_repo(path: Path) -> None:
    _git(path, "init")
    _git(path, "config", "user.email", "test@example.com")
    _git(path, "config", "user.name", "Test User")


def _commit_file(path: Path, file_name: str, content: str, message: str) -> None:
    (path / file_name).write_text(content, encoding="utf-8")
    _git(path, "add", file_name)
    _git(path, "commit", "-m", message)


def test_offline_handoff_exports_bundle_patch_and_instructions(tmp_path: Path) -> None:
    remote = tmp_path / "remote.git"
    _git(tmp_path, "init", "--bare", str(remote))

    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    _commit_file(repo, "README.md", "base\n", "base commit")
    _git(repo, "remote", "add", "origin", str(remote))

    branch = _git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    _git(repo, "push", "-u", "origin", branch)

    script_path = repo / "scripts" / "offline-handoff.sh"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SCRIPT, script_path)

    _commit_file(repo, "change.txt", "change\n", "offline change")

    timestamp = "20260310T000000Z"
    result = _run(["bash", str(script_path), "--timestamp", timestamp], cwd=repo)

    assert result.returncode == 0
    assert "HANDOFF|summary|PASS|" in result.stdout

    out_dir = repo / "artifacts" / "offline-handoff" / timestamp
    assert (out_dir / "branch-status.txt").exists()
    assert (out_dir / "commit-list.txt").exists()
    assert (out_dir / "offline.bundle").exists()
    assert (out_dir / "RESTORE_APPLY.md").exists()

    patches = list((out_dir / "patches").glob("*.patch"))
    assert patches

    summary = (out_dir / "handoff-summary.txt").read_text(encoding="utf-8")
    assert "Ahead: 1" in summary
    assert "Behind: 0" in summary
    assert "Bundle: CREATED" in summary
    assert "Patch series: CREATED" in summary

    commits = (out_dir / "commit-list.txt").read_text(encoding="utf-8")
    assert "offline change" in commits

    restore = (out_dir / "RESTORE_APPLY.md").read_text(encoding="utf-8")
    assert "git fetch /path/to/offline.bundle" in restore
    assert "git am /path/to/patches/*.patch" in restore


def test_offline_handoff_includes_sync_push_error_when_available(tmp_path: Path) -> None:
    remote = tmp_path / "remote.git"
    _git(tmp_path, "init", "--bare", str(remote))

    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    _commit_file(repo, "README.md", "base\n", "base commit")
    _git(repo, "remote", "add", "origin", str(remote))

    branch = _git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    _git(repo, "push", "-u", "origin", branch)

    script_path = repo / "scripts" / "offline-handoff.sh"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SCRIPT, script_path)

    _commit_file(repo, "change.txt", "change\n", "offline change")

    sync_report = repo / "dist" / "sync-submit-status-latest.txt"
    sync_report.parent.mkdir(parents=True, exist_ok=True)
    sync_report.write_text(
        "REMOTE_REACHABILITY_ERROR:\n"
        "fatal: unable to access 'https://example.invalid/repo.git/': Could not resolve host\n"
        "\n"
        "PUSH_FINAL_ERROR:\n"
        "fatal: unable to access 'https://example.invalid/repo.git/': Could not resolve host\n"
        "\n",
        encoding="utf-8",
    )

    timestamp = "20260310T010000Z"
    result = _run(["bash", str(script_path), "--timestamp", timestamp], cwd=repo)

    assert result.returncode == 0

    summary = (repo / "artifacts" / "offline-handoff" / timestamp / "handoff-summary.txt").read_text(
        encoding="utf-8"
    )
    assert "PUSH_FINAL_ERROR (from dist/sync-submit-status-latest.txt):" in summary
    assert "Could not resolve host" in summary
