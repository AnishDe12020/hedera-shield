#!/usr/bin/env python3
"""Capture immutable submission freeze manifest for HederaShield artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_ARTIFACT_PATTERNS = [
    "dist/submission-bundle.zip",
    "dist/release-evidence-*.tar.gz",
    "dist/submission-readiness-latest.txt",
    "dist/pre-submit-verify-latest.txt",
    "dist/sprint-status/sprint-dashboard-latest.md",
    "dist/sprint-status/sprint-dashboard-latest.json",
    "dist/sync-submit-status-latest.txt",
    "dist/network-recovery-push-status-latest.txt",
    "dist/network-recovery-push-status-latest.json",
    "artifacts/handoff-index/*/handoff-index.md",
    "artifacts/handoff-index/*/handoff-index.json",
]


@dataclass
class ArtifactSnapshot:
    key: str
    source_pattern: str
    path: str | None
    status: str
    sha256: str
    size_bytes: int
    details: str


def _now_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _now_iso_utc() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _run_git(root: Path, *cmd: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *cmd],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        env={"GIT_TERMINAL_PROMPT": "0"},
    )


def _latest_match(root: Path, pattern: str) -> Path | None:
    matches = sorted(root.glob(pattern))
    if not matches:
        return None
    return matches[-1]


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _rel(root: Path, path: Path) -> str:
    return str(path.resolve().relative_to(root.resolve()))


def _key_for_pattern(pattern: str) -> str:
    key = pattern.replace("*", "latest").replace("?", "x")
    for old, new in (("/", "_"), ("-", "_"), (".", "_")):
        key = key.replace(old, new)
    while "__" in key:
        key = key.replace("__", "_")
    return key.strip("_")


def _resolve_artifact(root: Path, pattern: str) -> ArtifactSnapshot:
    key = _key_for_pattern(pattern)
    if "*" in pattern or "?" in pattern:
        path = _latest_match(root, pattern)
    else:
        candidate = root / pattern
        path = candidate if candidate.exists() else None

    if path is None:
        return ArtifactSnapshot(
            key=key,
            source_pattern=pattern,
            path=None,
            status="MISSING",
            sha256="",
            size_bytes=0,
            details=f"missing {pattern}",
        )

    if not path.is_file():
        return ArtifactSnapshot(
            key=key,
            source_pattern=pattern,
            path=_rel(root, path),
            status="ERROR",
            sha256="",
            size_bytes=0,
            details=f"not a file: {_rel(root, path)}",
        )

    digest = _sha256(path)
    size = path.stat().st_size
    return ArtifactSnapshot(
        key=key,
        source_pattern=pattern,
        path=_rel(root, path),
        status="PASS",
        sha256=digest,
        size_bytes=size,
        details=f"sha256 {digest[:12]}...",
    )


def _repo_metadata(root: Path) -> dict[str, Any]:
    branch = _run_git(root, "rev-parse", "--abbrev-ref", "HEAD")
    commit = _run_git(root, "rev-parse", "HEAD")
    dirty = _run_git(root, "status", "--porcelain")

    branch_name = branch.stdout.strip() if branch.returncode == 0 else ""
    commit_sha = commit.stdout.strip() if commit.returncode == 0 else ""
    dirty_output = dirty.stdout.strip() if dirty.returncode == 0 else ""
    is_dirty = bool(dirty_output)

    return {
        "branch": branch_name,
        "commit_sha": commit_sha,
        "is_dirty": is_dirty,
        "git_status_porcelain": dirty_output,
    }


def _write_markdown_manifest(
    *,
    output_file: Path,
    timestamp_utc: str,
    generated_at_utc: str,
    repo: dict[str, Any],
    artifacts: list[ArtifactSnapshot],
) -> None:
    pass_count = sum(1 for item in artifacts if item.status == "PASS")
    missing_count = sum(1 for item in artifacts if item.status == "MISSING")
    error_count = sum(1 for item in artifacts if item.status == "ERROR")

    lines: list[str] = []
    lines.append("# HederaShield Submission Freeze Manifest")
    lines.append("")
    lines.append(f"- Timestamp (UTC): `{timestamp_utc}`")
    lines.append(f"- Generated At (UTC): `{generated_at_utc}`")
    lines.append(f"- Branch: `{repo.get('branch', '')}`")
    lines.append(f"- Commit SHA: `{repo.get('commit_sha', '')}`")
    lines.append(f"- Working Tree Dirty: `{repo.get('is_dirty', False)}`")
    lines.append("")
    lines.append("## Artifact Summary")
    lines.append(f"- PASS: {pass_count}")
    lines.append(f"- MISSING: {missing_count}")
    lines.append(f"- ERROR: {error_count}")
    lines.append("")
    lines.append("## Artifacts")
    lines.append("| Key | Status | Path | SHA256 | Size (bytes) | Source Pattern |")
    lines.append("| --- | --- | --- | --- | ---: | --- |")
    for item in artifacts:
        lines.append(
            "| "
            f"{item.key} | {item.status} | {item.path or '-'} | {item.sha256 or '-'} | "
            f"{item.size_bytes} | {item.source_pattern} |"
        )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def create_manifest(
    *,
    root: Path,
    output_dir: Path,
    timestamp_utc: str,
    artifact_patterns: list[str],
) -> tuple[Path, Path, list[ArtifactSnapshot]]:
    repo = _repo_metadata(root)
    generated_at = _now_iso_utc()
    artifacts = [_resolve_artifact(root, pattern) for pattern in artifact_patterns]

    payload = {
        "schema_version": "1.0",
        "manifest_type": "submission_freeze",
        "timestamp_utc": timestamp_utc,
        "generated_at_utc": generated_at,
        "repo": repo,
        "artifacts": [asdict(item) for item in artifacts],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    json_file = output_dir / f"submission-freeze-{timestamp_utc}.json"
    md_file = output_dir / f"submission-freeze-{timestamp_utc}.md"
    latest_json = output_dir / "submission-freeze-latest.json"
    latest_md = output_dir / "submission-freeze-latest.md"

    json_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_markdown_manifest(
        output_file=md_file,
        timestamp_utc=timestamp_utc,
        generated_at_utc=generated_at,
        repo=repo,
        artifacts=artifacts,
    )

    shutil.copyfile(json_file, latest_json)
    shutil.copyfile(md_file, latest_md)

    return json_file, md_file, artifacts


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="dist/submission-freeze",
        help="Output directory for freeze manifests (default: dist/submission-freeze)",
    )
    parser.add_argument(
        "--timestamp",
        default="",
        help="Optional UTC timestamp override in format YYYYMMDDTHHMMSSZ",
    )
    parser.add_argument(
        "--artifact",
        action="append",
        default=[],
        help="Optional artifact path/pattern to include. Repeatable. Uses defaults when omitted.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    root = Path(__file__).resolve().parent.parent
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = root / output_dir

    timestamp_utc = args.timestamp or _now_timestamp()
    patterns = args.artifact if args.artifact else DEFAULT_ARTIFACT_PATTERNS

    json_file, md_file, artifacts = create_manifest(
        root=root,
        output_dir=output_dir,
        timestamp_utc=timestamp_utc,
        artifact_patterns=patterns,
    )

    missing = sum(1 for item in artifacts if item.status == "MISSING")
    errors = sum(1 for item in artifacts if item.status == "ERROR")
    overall = "PASS" if errors == 0 else "FAIL"

    print(f"FREEZE|manifest_json|PASS|wrote {json_file.relative_to(root)}")
    print(f"FREEZE|manifest_md|PASS|wrote {md_file.relative_to(root)}")
    print("FREEZE|manifest_latest_json|PASS|updated dist/submission-freeze/submission-freeze-latest.json")
    print("FREEZE|manifest_latest_md|PASS|updated dist/submission-freeze/submission-freeze-latest.md")
    print(f"FREEZE|summary|{overall}|artifacts={len(artifacts)} missing={missing} errors={errors}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
