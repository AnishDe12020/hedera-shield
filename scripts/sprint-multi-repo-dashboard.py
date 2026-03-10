#!/usr/bin/env python3
"""Generate a consolidated multi-repo sprint push dashboard."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_REPOS = [
    {"name": "gitlab", "path": ".", "remote": "origin"},
    {"name": "hedera", "path": ".", "remote": "origin"},
    {"name": "do", "path": ".", "remote": "origin"},
]

LATEST_ARTIFACT_PATTERNS = {
    "submission_readiness_latest": "dist/submission-readiness-latest.txt",
    "pre_submit_verify_latest": "dist/pre-submit-verify-latest.txt",
    "sync_submit_latest": "dist/sync-submit-status-latest.txt",
    "network_recovery_text_latest": "dist/network-recovery-push-status-latest.txt",
    "network_recovery_json_latest": "dist/network-recovery-push-status-latest.json",
    "handoff_index_latest_md": "artifacts/handoff-index/*/handoff-index.md",
    "handoff_index_latest_json": "artifacts/handoff-index/*/handoff-index.json",
}


@dataclass
class RepoSpec:
    name: str
    path: Path
    remote: str = "origin"


@dataclass
class RepoStatus:
    name: str
    path: str
    remote: str
    remote_url: str
    branch: str
    upstream: str
    ahead_count: int
    behind_count: int
    latest_commit: dict[str, str]
    remote_reachability: dict[str, str]
    latest_status_artifacts: dict[str, str]
    attempt_push: dict[str, Any]
    status: str
    details: str


def _now_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _run(cwd: Path, *cmd: str) -> subprocess.CompletedProcess[str]:
    env = {"GIT_TERMINAL_PROMPT": "0"}
    return subprocess.run(
        list(cmd),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def _latest_match(root: Path, pattern: str) -> Path | None:
    matches = sorted(root.glob(pattern))
    if not matches:
        return None
    return matches[-1]


def _extract_named_block(report_text: str, header: str) -> str:
    lines = report_text.splitlines()
    out: list[str] = []
    in_block = False
    for line in lines:
        if in_block and line.strip() == "":
            break
        if in_block:
            out.append(line)
        elif line.strip() == header:
            in_block = True
    return "\n".join(out).strip()


def _rel(base: Path, path: Path) -> str:
    return str(path.resolve().relative_to(base.resolve()))


def _repo_rel(root: Path, path: Path) -> str:
    try:
        return _rel(root, path)
    except ValueError:
        return str(path.resolve())


def _discover_latest_artifacts(repo_path: Path) -> dict[str, str]:
    results: dict[str, str] = {}
    for key, pattern in LATEST_ARTIFACT_PATTERNS.items():
        if "*" in pattern or "?" in pattern:
            match = _latest_match(repo_path, pattern)
        else:
            candidate = repo_path / pattern
            match = candidate if candidate.exists() else None
        if match is not None and match.exists():
            results[key] = _repo_rel(repo_path, match)
    return results


def _parse_repo_arg(value: str, root: Path) -> RepoSpec:
    if "=" not in value:
        raise ValueError(f"--repo must use NAME=PATH format: {value!r}")
    name, raw_path = value.split("=", 1)
    name = name.strip().lower()
    raw_path = raw_path.strip()
    if not name or not raw_path:
        raise ValueError(f"invalid --repo value: {value!r}")
    path = Path(raw_path)
    if not path.is_absolute():
        path = (root / path).resolve()
    return RepoSpec(name=name, path=path)


def _load_repo_specs(root: Path, repo_config: Path | None, repo_args: list[str]) -> list[RepoSpec]:
    specs: list[RepoSpec] = []
    if repo_config is not None:
        payload = json.loads(repo_config.read_text(encoding="utf-8"))
        repos = payload.get("repos", [])
        if not isinstance(repos, list):
            raise ValueError("repo config must contain a top-level 'repos' list")
        for item in repos:
            if not isinstance(item, dict):
                raise ValueError("each repo config entry must be an object")
            name = str(item.get("name", "")).strip().lower()
            path_value = str(item.get("path", "")).strip()
            remote = str(item.get("remote", "origin")).strip() or "origin"
            if not name or not path_value:
                raise ValueError("each repo config entry requires non-empty name and path")
            path = Path(path_value)
            if not path.is_absolute():
                path = (root / path).resolve()
            specs.append(RepoSpec(name=name, path=path, remote=remote))

    if repo_args:
        specs = [_parse_repo_arg(raw, root) for raw in repo_args]

    if not specs:
        specs = [
            RepoSpec(
                name=str(item["name"]),
                path=(root / str(item["path"])).resolve(),
                remote=str(item["remote"]),
            )
            for item in DEFAULT_REPOS
        ]

    return specs


def _git_branch(repo_path: Path) -> str:
    result = _run(repo_path, "git", "rev-parse", "--abbrev-ref", "HEAD")
    return result.stdout.strip() if result.returncode == 0 else ""


def _git_upstream(repo_path: Path, branch: str) -> str:
    if not branch or branch == "HEAD":
        return ""
    result = _run(repo_path, "git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", f"{branch}@{{upstream}}")
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _git_counts(repo_path: Path, upstream: str) -> tuple[int, int]:
    if upstream:
        result = _run(repo_path, "git", "rev-list", "--left-right", "--count", f"{upstream}...HEAD")
        if result.returncode == 0:
            parts = result.stdout.strip().split()
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                return int(parts[1]), int(parts[0])
    result = _run(repo_path, "git", "rev-list", "--count", "HEAD")
    if result.returncode == 0 and result.stdout.strip().isdigit():
        return int(result.stdout.strip()), 0
    return 0, 0


def _git_latest_commit(repo_path: Path) -> dict[str, str]:
    result = _run(repo_path, "git", "log", "-1", "--pretty=format:%H%x1f%cI%x1f%s")
    if result.returncode != 0:
        return {"sha": "", "timestamp": "", "subject": ""}
    parts = result.stdout.split("\x1f", 2)
    while len(parts) < 3:
        parts.append("")
    return {"sha": parts[0], "timestamp": parts[1], "subject": parts[2]}


def _remote_url(repo_path: Path, remote: str) -> str:
    result = _run(repo_path, "git", "remote", "get-url", remote)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _remote_reachability(repo_path: Path, remote: str) -> dict[str, str]:
    result = _run(repo_path, "git", "ls-remote", "--heads", remote)
    error = (result.stdout + result.stderr).strip()
    if result.returncode == 0:
        return {"status": "PASS", "error": ""}
    return {"status": "FAIL", "error": error}


def _attempt_push_with_helper(
    *,
    repo_path: Path,
    repo_name: str,
    helper_script: str,
    remote: str,
    branch: str,
    timestamp_utc: str,
) -> dict[str, Any]:
    helper = repo_path / helper_script
    if not helper.exists():
        return {
            "attempted": True,
            "status": "FAIL",
            "reason": "missing_helper",
            "helper": helper_script,
            "error": f"missing helper script: {helper_script}",
            "exit_code": 1,
            "report_path": "",
            "remote_reachability_error": "",
        }

    dist_dir = repo_path / "dist" / "sprint-status"
    dist_dir.mkdir(parents=True, exist_ok=True)
    report_path = dist_dir / f"sync-submit-attempt-{timestamp_utc}-{repo_name}.txt"

    result = _run(
        repo_path,
        "bash",
        str(helper),
        "--remote",
        remote,
        "--branch",
        branch,
        "--max-retries",
        "1",
        "--initial-backoff-seconds",
        "0",
        "--max-backoff-seconds",
        "1",
        "--report-file",
        str(report_path),
    )

    report_text = report_path.read_text(encoding="utf-8", errors="replace") if report_path.exists() else ""
    push_error = _extract_named_block(report_text, "PUSH_FINAL_ERROR:")
    remote_error = _extract_named_block(report_text, "REMOTE_REACHABILITY_ERROR:")
    combined_error = (push_error or remote_error or (result.stdout + result.stderr)).strip()
    status = "PASS" if result.returncode == 0 else "FAIL"
    details = "helper push completed" if status == "PASS" else "helper push failed"
    return {
        "attempted": True,
        "status": status,
        "reason": details,
        "helper": helper_script,
        "exit_code": result.returncode,
        "report_path": _repo_rel(repo_path, report_path),
        "error": combined_error,
        "remote_reachability_error": remote_error,
    }


def _collect_repo_status(
    *,
    root: Path,
    spec: RepoSpec,
    attempt_push: bool,
    helper_script: str,
    timestamp_utc: str,
) -> RepoStatus:
    repo_path = spec.path.resolve()

    if not repo_path.exists():
        return RepoStatus(
            name=spec.name,
            path=_repo_rel(root, repo_path),
            remote=spec.remote,
            remote_url="",
            branch="",
            upstream="",
            ahead_count=0,
            behind_count=0,
            latest_commit={"sha": "", "timestamp": "", "subject": ""},
            remote_reachability={"status": "FAIL", "error": "repository path does not exist"},
            latest_status_artifacts={},
            attempt_push={
                "attempted": False,
                "status": "SKIPPED",
                "reason": "missing_repository_path",
                "error": "",
            },
            status="FAIL",
            details="repository path does not exist",
        )

    if _run(repo_path, "git", "rev-parse", "--is-inside-work-tree").returncode != 0:
        return RepoStatus(
            name=spec.name,
            path=_repo_rel(root, repo_path),
            remote=spec.remote,
            remote_url="",
            branch="",
            upstream="",
            ahead_count=0,
            behind_count=0,
            latest_commit={"sha": "", "timestamp": "", "subject": ""},
            remote_reachability={"status": "FAIL", "error": "path is not a git repository"},
            latest_status_artifacts=_discover_latest_artifacts(repo_path),
            attempt_push={
                "attempted": False,
                "status": "SKIPPED",
                "reason": "not_a_git_repository",
                "error": "",
            },
            status="FAIL",
            details="path is not a git repository",
        )

    remote_url = _remote_url(repo_path, spec.remote)
    branch = _git_branch(repo_path)
    upstream = _git_upstream(repo_path, branch)
    ahead_count, behind_count = _git_counts(repo_path, upstream)
    latest_commit = _git_latest_commit(repo_path)
    artifacts = _discover_latest_artifacts(repo_path)

    if not remote_url:
        reachability = {"status": "FAIL", "error": f"remote '{spec.remote}' is not configured"}
    else:
        reachability = _remote_reachability(repo_path, spec.remote)

    attempt_state: dict[str, Any] = {
        "attempted": False,
        "status": "SKIPPED",
        "reason": "read_only_mode",
        "error": "",
    }
    if attempt_push:
        if reachability["status"] != "PASS":
            attempt_state = {
                "attempted": False,
                "status": "SKIPPED",
                "reason": "remote_unreachable",
                "error": reachability["error"],
            }
        else:
            attempt_state = _attempt_push_with_helper(
                repo_path=repo_path,
                repo_name=spec.name,
                helper_script=helper_script,
                remote=spec.remote,
                branch=branch,
                timestamp_utc=timestamp_utc,
            )

    repo_status = "PASS"
    details = "dashboard status collected"
    if reachability["status"] != "PASS":
        repo_status = "WARN"
        details = "remote unreachable"
    if attempt_push and attempt_state.get("status") == "FAIL":
        repo_status = "FAIL"
        details = "push attempt failed"
    if attempt_push and attempt_state.get("status") == "SKIPPED" and attempt_state.get("reason") == "remote_unreachable":
        repo_status = "WARN"
        details = "push skipped (remote unreachable)"

    return RepoStatus(
        name=spec.name,
        path=_repo_rel(root, repo_path),
        remote=spec.remote,
        remote_url=remote_url,
        branch=branch,
        upstream=upstream,
        ahead_count=ahead_count,
        behind_count=behind_count,
        latest_commit=latest_commit,
        remote_reachability=reachability,
        latest_status_artifacts=artifacts,
        attempt_push=attempt_state,
        status=repo_status,
        details=details,
    )


def _render_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# HederaShield Multi-Repo Sprint Push Dashboard")
    lines.append("")
    lines.append(f"- Timestamp (UTC): `{payload['timestamp_utc']}`")
    lines.append(f"- Generated at (UTC): `{payload['generated_at_utc']}`")
    lines.append(f"- Attempt push enabled: `{payload['attempt_push']}`")
    lines.append(f"- Overall status: `{payload['summary']['overall']}`")
    lines.append(
        "- Summary counts: "
        f"PASS={payload['summary']['pass']} "
        f"WARN={payload['summary']['warn']} "
        f"FAIL={payload['summary']['fail']}"
    )
    lines.append("")
    lines.append("## Repo Summary")
    lines.append("| Repo | Branch | Ahead | Behind | Remote Reachability | Status |")
    lines.append("|---|---|---:|---:|---|---|")
    for repo in payload["repos"]:
        lines.append(
            "| "
            f"`{repo['name']}` | "
            f"`{repo['branch'] or '-'}` | "
            f"`{repo['ahead_count']}` | "
            f"`{repo['behind_count']}` | "
            f"`{repo['remote_reachability']['status']}` | "
            f"`{repo['status']}` |"
        )

    lines.append("")
    lines.append("## Repo Details")
    for repo in payload["repos"]:
        lines.append(f"### `{repo['name']}`")
        lines.append(f"- Path: `{repo['path']}`")
        lines.append(f"- Remote: `{repo['remote']}`")
        lines.append(f"- Remote URL: `{repo['remote_url'] or '-'}`")
        lines.append(f"- Branch: `{repo['branch'] or '-'}`")
        lines.append(f"- Upstream: `{repo['upstream'] or '-'}`")
        lines.append(
            "- Latest commit: "
            f"`{repo['latest_commit']['sha'][:12] if repo['latest_commit']['sha'] else '-'}` "
            f"`{repo['latest_commit']['timestamp'] or '-'}` "
            f"{repo['latest_commit']['subject'] or '-'}"
        )
        lines.append(f"- Ahead/Behind: `{repo['ahead_count']}/{repo['behind_count']}`")
        lines.append(f"- Remote reachability: `{repo['remote_reachability']['status']}`")
        if repo["remote_reachability"]["error"]:
            lines.append("  - Reachability error:")
            lines.append("```text")
            lines.append(repo["remote_reachability"]["error"])
            lines.append("```")
        lines.append(
            f"- Push attempt: `{repo['attempt_push'].get('status', 'SKIPPED')}` "
            f"({repo['attempt_push'].get('reason', '')})"
        )
        if repo["attempt_push"].get("report_path"):
            lines.append(f"- Push helper report: `{repo['attempt_push']['report_path']}`")
        if repo["attempt_push"].get("error"):
            lines.append("  - Push/Sync error:")
            lines.append("```text")
            lines.append(repo["attempt_push"]["error"])
            lines.append("```")

        artifacts = repo["latest_status_artifacts"]
        if artifacts:
            lines.append("- Latest status artifacts:")
            for key in sorted(artifacts):
                lines.append(f"  - `{key}`: `{artifacts[key]}`")
        else:
            lines.append("- Latest status artifacts: `<none found>`")
        lines.append("")

    return "\n".join(lines)


def _summary(statuses: list[RepoStatus]) -> dict[str, Any]:
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for item in statuses:
        counts[item.status] = counts.get(item.status, 0) + 1
    overall = "PASS"
    if counts["FAIL"] > 0:
        overall = "FAIL"
    elif counts["WARN"] > 0:
        overall = "WARN"
    return {
        "overall": overall,
        "pass": counts["PASS"],
        "warn": counts["WARN"],
        "fail": counts["FAIL"],
        "total": len(statuses),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate multi-repo sprint push dashboard (markdown + json)")
    parser.add_argument("--timestamp", default=_now_timestamp(), help="UTC timestamp in YYYYMMDDTHHMMSSZ")
    parser.add_argument("--output-base-dir", default="dist/sprint-status", help="Dashboard output directory base")
    parser.add_argument("--repo-config", default="", help="Optional JSON config containing top-level repos list")
    parser.add_argument(
        "--repo",
        action="append",
        default=[],
        help="Override repo set with NAME=PATH entries (repeatable). Default: gitlab/hedera/do -> current repo",
    )
    parser.add_argument("--attempt-push", action="store_true", help="Attempt safe push via sync helper when reachable")
    parser.add_argument(
        "--sync-helper-script",
        default="scripts/sync-and-submit.sh",
        help="Per-repo helper script path used with --attempt-push",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    repo_config = Path(args.repo_config).resolve() if args.repo_config else None
    if repo_config is not None and not repo_config.exists():
        print(f"SPRINT_DASH|config|FAIL|missing repo config: {repo_config}")
        return 2

    try:
        specs = _load_repo_specs(root, repo_config, args.repo)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"SPRINT_DASH|config|FAIL|{exc}")
        return 2

    statuses = [
        _collect_repo_status(
            root=root,
            spec=spec,
            attempt_push=args.attempt_push,
            helper_script=args.sync_helper_script,
            timestamp_utc=args.timestamp,
        )
        for spec in specs
    ]

    output_dir = (root / args.output_base_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / f"sprint-dashboard-{args.timestamp}.md"
    json_path = output_dir / f"sprint-dashboard-{args.timestamp}.json"
    latest_md = output_dir / "sprint-dashboard-latest.md"
    latest_json = output_dir / "sprint-dashboard-latest.json"

    payload: dict[str, Any] = {
        "timestamp_utc": args.timestamp,
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "attempt_push": args.attempt_push,
        "output_dir": _rel(root, output_dir),
        "summary": _summary(statuses),
        "repos": [asdict(item) for item in statuses],
    }

    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(_render_markdown(payload), encoding="utf-8")
    shutil.copyfile(md_path, latest_md)
    shutil.copyfile(json_path, latest_json)

    print(f"SPRINT_DASH|output_dir|PASS|{_rel(root, output_dir)}")
    print(f"SPRINT_DASH|markdown|PASS|{_rel(root, md_path)}")
    print(f"SPRINT_DASH|json|PASS|{_rel(root, json_path)}")
    print(f"SPRINT_DASH|markdown_latest|PASS|{_rel(root, latest_md)}")
    print(f"SPRINT_DASH|json_latest|PASS|{_rel(root, latest_json)}")
    print(
        "SPRINT_DASH|summary|"
        f"{payload['summary']['overall']}|"
        f"PASS={payload['summary']['pass']} WARN={payload['summary']['warn']} FAIL={payload['summary']['fail']}"
    )

    if args.attempt_push and payload["summary"]["fail"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
