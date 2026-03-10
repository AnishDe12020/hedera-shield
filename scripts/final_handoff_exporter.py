#!/usr/bin/env python3
"""Cross-repo final handoff exporter.

Collects latest key handoff artifacts from multiple repositories into one
consolidated package under dist/final-handoff/.

Behavioral contract:
- Read-only against source repos.
- Writes only under this repo's output directory.
- Produces markdown + json master indexes with absolute paths, existence flags,
  and quick restore/use notes.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ArtifactSpec:
    key: str
    label: str
    expected_rel_hints: list[str]
    patterns: list[str]
    quick_use_note: str
    quick_restore_note: str
    max_items: int = 1


@dataclass
class ArtifactEntry:
    key: str
    label: str
    expected_abs_hints: list[str]
    source_abs_path: str | None
    exists: bool
    copied_abs_path: str | None
    copied_rel_path: str | None
    quick_use_note: str
    quick_restore_note: str


@dataclass
class RepoSnapshot:
    name: str
    slug: str
    path: str
    exists: bool
    is_git_repo: bool
    branch: str
    head_commit: str
    artifacts: dict[str, ArtifactEntry | list[ArtifactEntry]]


ARTIFACT_SPECS: list[ArtifactSpec] = [
    ArtifactSpec(
        key="submission_freeze_manifest_json",
        label="Submission Freeze Manifest (JSON)",
        expected_rel_hints=[
            "dist/submission-freeze/submission-freeze-latest.json",
            "artifacts/submission-freeze/submission-freeze-latest.json",
            "docs/evidence/submission-freeze/submission-freeze-latest.json",
        ],
        patterns=[
            "dist/submission-freeze/submission-freeze-latest.json",
            "dist/submission-freeze/submission-freeze-20*.json",
            "artifacts/submission-freeze/submission-freeze-latest.json",
            "artifacts/submission-freeze/submission-freeze-20*.json",
            "docs/evidence/submission-freeze/submission-freeze-latest.json",
            "docs/evidence/submission-freeze/submission-freeze-20*.json",
        ],
        quick_use_note="Use as immutable snapshot baseline for final submission state.",
        quick_restore_note=(
            "Regenerate in source repo: submission-freeze script "
            "(e.g., ./scripts/submission-freeze.py or ./scripts/submission-freeze.sh)."
        ),
    ),
    ArtifactSpec(
        key="submission_freeze_manifest_markdown",
        label="Submission Freeze Manifest (Markdown)",
        expected_rel_hints=[
            "dist/submission-freeze/submission-freeze-latest.md",
            "artifacts/submission-freeze/submission-freeze-latest.md",
            "docs/evidence/submission-freeze/submission-freeze-latest.md",
        ],
        patterns=[
            "dist/submission-freeze/submission-freeze-latest.md",
            "dist/submission-freeze/submission-freeze-20*.md",
            "artifacts/submission-freeze/submission-freeze-latest.md",
            "artifacts/submission-freeze/submission-freeze-20*.md",
            "docs/evidence/submission-freeze/submission-freeze-latest.md",
            "docs/evidence/submission-freeze/submission-freeze-20*.md",
        ],
        quick_use_note="Use for human-readable freeze evidence review.",
        quick_restore_note=(
            "Regenerate in source repo: submission-freeze script "
            "(e.g., ./scripts/submission-freeze.py or ./scripts/submission-freeze.sh)."
        ),
    ),
    ArtifactSpec(
        key="handoff_index_json",
        label="Handoff Index (JSON)",
        expected_rel_hints=[
            "artifacts/handoff-index/handoff-index-latest.json",
            "artifacts/handoff-index/<timestamp>/handoff-index.json",
        ],
        patterns=[
            "artifacts/handoff-index/handoff-index-latest.json",
            "artifacts/handoff-index/handoff-index-20*.json",
            "artifacts/handoff-index/*/handoff-index.json",
        ],
        quick_use_note="Use for machine-readable handoff navigation.",
        quick_restore_note="Regenerate in source repo with its handoff-index generator script.",
    ),
    ArtifactSpec(
        key="handoff_index_markdown",
        label="Handoff Index (Markdown)",
        expected_rel_hints=[
            "artifacts/handoff-index/handoff-index-latest.md",
            "artifacts/handoff-index/<timestamp>/handoff-index.md",
            "artifacts/handoff-index/<timestamp>/HANDOFF_INDEX.md",
        ],
        patterns=[
            "artifacts/handoff-index/handoff-index-latest.md",
            "artifacts/handoff-index/handoff-index-20*.md",
            "artifacts/handoff-index/*/handoff-index.md",
            "artifacts/handoff-index/*/HANDOFF_INDEX.md",
        ],
        quick_use_note="Use for human-readable handoff checklist and links.",
        quick_restore_note="Regenerate in source repo with its handoff-index generator script.",
    ),
    ArtifactSpec(
        key="sync_status_artifact",
        label="Sync Status Artifact",
        expected_rel_hints=[
            "dist/sync-submit-status-latest.txt",
            "artifacts/submission-status/sync-submit-status.txt",
            "docs/evidence/sync-submit-status-<timestamp>.md",
        ],
        patterns=[
            "dist/sync-submit-status-latest.txt",
            "dist/sync-submit-status-20*.txt",
            "artifacts/submission-status/sync-submit-status.txt",
            "docs/evidence/sync-submit-status-20*.md",
        ],
        quick_use_note="Use to verify ahead/behind and last sync outcome.",
        quick_restore_note="Regenerate in source repo with sync-submit helper (e.g., ./scripts/sync-and-submit.sh).",
    ),
    ArtifactSpec(
        key="push_status_json",
        label="Push/Network Status Artifact (JSON)",
        expected_rel_hints=[
            "dist/network-recovery-push-status-latest.json",
            "artifacts/submission-status/network-recovery-push-status-latest.json",
            "docs/evidence/submission-freeze/push-status-latest.json",
        ],
        patterns=[
            "dist/network-recovery-push-status-latest.json",
            "dist/network-recovery-push-status-20*.json",
            "artifacts/submission-status/network-recovery-push-status-latest.json",
            "artifacts/submission-status/network-recovery-push-status-20*.json",
            "docs/evidence/submission-freeze/push-status-latest.json",
            "docs/evidence/submission-freeze/push-status-20*.json",
        ],
        quick_use_note="Use for exact structured push/network error state.",
        quick_restore_note="Regenerate via network-recovery push tooling in source repo.",
    ),
    ArtifactSpec(
        key="push_status_text",
        label="Push/Network Status Artifact (Text/Markdown)",
        expected_rel_hints=[
            "dist/network-recovery-push-status-latest.txt",
            "dist/git-push-status-latest.txt",
            "artifacts/submission-status/network-recovery-push-status-latest.txt",
            "docs/evidence/submission-freeze/push-status-latest.md",
        ],
        patterns=[
            "dist/network-recovery-push-status-latest.txt",
            "dist/network-recovery-push-status-20*.txt",
            "dist/git-push-status-latest.txt",
            "dist/git-push-status-20*.txt",
            "artifacts/submission-status/network-recovery-push-status-latest.txt",
            "artifacts/submission-status/network-recovery-push-status-20*.txt",
            "docs/evidence/submission-freeze/push-status-latest.md",
            "docs/evidence/submission-freeze/push-status-20*.md",
            "docs/evidence/network-recovery-push-status-20*.md",
        ],
        quick_use_note="Use for plain-text troubleshooting details and retry context.",
        quick_restore_note="Regenerate via sync-submit/network-recovery tooling in source repo.",
    ),
    ArtifactSpec(
        key="submission_bundle",
        label="Submission Bundle ZIP",
        expected_rel_hints=[
            "dist/submission-bundle.zip",
            "submission-bundle.zip",
            "artifacts/demo-recording/submission-bundle.zip",
        ],
        patterns=[
            "dist/submission-bundle.zip",
            "submission-bundle.zip",
            "artifacts/demo-recording/submission-bundle.zip",
        ],
        quick_use_note="Use as the packaged upload artifact when submitting.",
        quick_restore_note="Regenerate in source repo with package-submission script.",
    ),
]


def utc_now() -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    return now.strftime("%Y%m%dT%H%M%SZ"), now.strftime("%Y-%m-%dT%H:%M:%SZ")


def sanitize_slug(value: str) -> str:
    chars: list[str] = []
    for ch in value.lower():
        chars.append(ch if ch.isalnum() else "-")
    slug = "".join(chars).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "repo"


def run(cmd: list[str], cwd: Path, timeout: int = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False, timeout=timeout)


def parse_repo_spec(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("--repo must be NAME=PATH")
    name, path_str = value.split("=", 1)
    name = name.strip()
    path_str = path_str.strip()
    if not name or not path_str:
        raise argparse.ArgumentTypeError("--repo must be NAME=PATH")
    return name, Path(path_str).expanduser().resolve()


def default_repo_specs(repo_root: Path) -> list[tuple[str, Path]]:
    return [
        ("gitlab-codeguard", Path("/home/anish/gitlab-codeguard").resolve()),
        ("hedera-shield", repo_root.resolve()),
        ("do-gradient-guard", Path("/home/anish/do-gradient-guard").resolve()),
    ]


def is_git_repo(path: Path) -> bool:
    return run(["git", "rev-parse", "--is-inside-work-tree"], cwd=path).returncode == 0


def git_branch(path: Path) -> str:
    cp = run(["git", "branch", "--show-current"], cwd=path)
    branch = cp.stdout.strip()
    return branch or "detached"


def git_head(path: Path) -> str:
    cp = run(["git", "rev-parse", "HEAD"], cwd=path)
    return cp.stdout.strip() if cp.returncode == 0 else ""


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    deduped: dict[str, Path] = {}
    for path in paths:
        deduped[str(path.resolve())] = path.resolve()
    return list(deduped.values())


def find_latest_candidates(repo_path: Path, patterns: list[str], max_items: int) -> list[Path]:
    matches: list[Path] = []
    for pattern in patterns:
        matches.extend([candidate for candidate in repo_path.glob(pattern) if candidate.is_file()])

    deduped = _dedupe_paths(matches)
    sorted_paths = sorted(
        deduped,
        key=lambda candidate: (candidate.stat().st_mtime, str(candidate)),
        reverse=True,
    )
    return sorted_paths[:max_items]


def copy_entry(source: Path, package_dir: Path, slug: str, key: str) -> tuple[str, str]:
    target_dir = package_dir / "collected" / slug / key
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / source.name
    shutil.copy2(source, target_path)
    return str(target_path.resolve()), str(target_path.relative_to(package_dir))


def collect_repo_snapshot(name: str, repo_path: Path, package_dir: Path) -> RepoSnapshot:
    exists = repo_path.exists()
    slug = sanitize_slug(name)

    if not exists:
        artifacts: dict[str, ArtifactEntry | list[ArtifactEntry]] = {}
        for spec in ARTIFACT_SPECS:
            expected_hints = [str((repo_path / rel).resolve()) for rel in spec.expected_rel_hints]
            if spec.max_items == 1:
                artifacts[spec.key] = ArtifactEntry(
                    key=spec.key,
                    label=spec.label,
                    expected_abs_hints=expected_hints,
                    source_abs_path=None,
                    exists=False,
                    copied_abs_path=None,
                    copied_rel_path=None,
                    quick_use_note=spec.quick_use_note,
                    quick_restore_note=spec.quick_restore_note,
                )
            else:
                artifacts[spec.key] = []

        return RepoSnapshot(
            name=name,
            slug=slug,
            path=str(repo_path),
            exists=False,
            is_git_repo=False,
            branch="",
            head_commit="",
            artifacts=artifacts,
        )

    repo_is_git = is_git_repo(repo_path)
    branch = git_branch(repo_path) if repo_is_git else ""
    head_commit = git_head(repo_path) if repo_is_git else ""

    artifacts_payload: dict[str, ArtifactEntry | list[ArtifactEntry]] = {}
    for spec in ARTIFACT_SPECS:
        expected_hints = [str((repo_path / rel).resolve()) for rel in spec.expected_rel_hints]
        found = find_latest_candidates(repo_path=repo_path, patterns=spec.patterns, max_items=spec.max_items)

        if spec.max_items == 1:
            chosen = found[0] if found else None
            source_abs = str(chosen.resolve()) if chosen is not None else None
            copied_abs = None
            copied_rel = None
            exists_flag = chosen is not None

            if chosen is not None:
                copied_abs, copied_rel = copy_entry(chosen, package_dir, slug, spec.key)

            artifacts_payload[spec.key] = ArtifactEntry(
                key=spec.key,
                label=spec.label,
                expected_abs_hints=expected_hints,
                source_abs_path=source_abs,
                exists=exists_flag,
                copied_abs_path=copied_abs,
                copied_rel_path=copied_rel,
                quick_use_note=spec.quick_use_note,
                quick_restore_note=spec.quick_restore_note,
            )
            continue

        items: list[ArtifactEntry] = []
        for item in found:
            copied_abs, copied_rel = copy_entry(item, package_dir, slug, spec.key)
            items.append(
                ArtifactEntry(
                    key=spec.key,
                    label=spec.label,
                    expected_abs_hints=expected_hints,
                    source_abs_path=str(item.resolve()),
                    exists=True,
                    copied_abs_path=copied_abs,
                    copied_rel_path=copied_rel,
                    quick_use_note=spec.quick_use_note,
                    quick_restore_note=spec.quick_restore_note,
                )
            )
        artifacts_payload[spec.key] = items

    return RepoSnapshot(
        name=name,
        slug=slug,
        path=str(repo_path),
        exists=True,
        is_git_repo=repo_is_git,
        branch=branch,
        head_commit=head_commit,
        artifacts=artifacts_payload,
    )


def repo_to_dict(repo: RepoSnapshot) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": repo.name,
        "slug": repo.slug,
        "path_abs": repo.path,
        "exists": repo.exists,
        "is_git_repo": repo.is_git_repo,
        "branch": repo.branch,
        "head_commit": repo.head_commit,
        "artifacts": {},
    }

    for key, value in repo.artifacts.items():
        if isinstance(value, list):
            payload["artifacts"][key] = [asdict(item) for item in value]
        else:
            payload["artifacts"][key] = asdict(value)

    return payload


def summarize(repos: list[RepoSnapshot]) -> dict[str, int]:
    total = 0
    found = 0
    for repo in repos:
        for value in repo.artifacts.values():
            if isinstance(value, list):
                total += len(value)
                found += len(value)
            else:
                total += 1
                if value.exists:
                    found += 1

    return {
        "repos_total": len(repos),
        "artifacts_total": total,
        "artifacts_found": found,
        "artifacts_missing": total - found,
    }


def _append_artifact_block(lines: list[str], key: str, entry: ArtifactEntry) -> None:
    lines.append(f"### {key}")
    lines.append(f"- label: `{entry.label}`")
    lines.append(f"- exists: `{str(entry.exists).lower()}`")
    lines.append(f"- expected_abs_hints: `{', '.join(entry.expected_abs_hints)}`")
    lines.append(f"- source_abs_path: `{entry.source_abs_path or 'missing'}`")
    lines.append(f"- copied_abs_path: `{entry.copied_abs_path or 'missing'}`")
    lines.append(f"- quick_use_note: {entry.quick_use_note}")
    lines.append(f"- quick_restore_note: {entry.quick_restore_note}")
    lines.append("")


def render_markdown(
    *,
    generated_at: str,
    timestamp: str,
    package_dir: Path,
    repos: list[RepoSnapshot],
    summary: dict[str, int],
) -> str:
    lines: list[str] = []
    lines.append("# Cross-Repo Final Handoff Master Index")
    lines.append("")
    lines.append(f"generated_at_utc: {generated_at}")
    lines.append(f"timestamp: {timestamp}")
    lines.append(f"package_dir_abs: {package_dir.resolve()}")
    lines.append("read_only_collection: true")
    lines.append(f"repos_total: {summary['repos_total']}")
    lines.append(f"artifacts_total: {summary['artifacts_total']}")
    lines.append(f"artifacts_found: {summary['artifacts_found']}")
    lines.append(f"artifacts_missing: {summary['artifacts_missing']}")
    lines.append("")

    lines.append("## Quick Restore/Use Notes")
    lines.append("- All source paths are absolute and are never modified by this exporter.")
    lines.append("- Re-run source repo freeze/handoff/sync scripts if any expected artifact is missing.")
    lines.append("- Use copied artifacts under this package for a self-contained final handoff.")
    lines.append("")

    for repo in repos:
        lines.append(f"## {repo.name}")
        lines.append(f"- repo_path_abs: `{repo.path}`")
        lines.append(f"- exists: `{str(repo.exists).lower()}`")
        lines.append(f"- is_git_repo: `{str(repo.is_git_repo).lower()}`")
        lines.append(f"- branch: `{repo.branch or 'n/a'}`")
        lines.append(f"- head_commit: `{repo.head_commit or 'n/a'}`")
        lines.append("")

        for key, value in repo.artifacts.items():
            if isinstance(value, list):
                lines.append(f"### {key}")
                if not value:
                    lines.append("- status: `missing`")
                    lines.append("")
                for entry in value:
                    _append_artifact_block(lines, key, entry)
                continue
            _append_artifact_block(lines, key, value)

    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cross-repo final handoff exporter")
    parser.add_argument(
        "--repo",
        action="append",
        default=[],
        metavar="NAME=PATH",
        help="Repeatable repo mapping. Default: gitlab-codeguard, hedera-shield, do-gradient-guard.",
    )
    parser.add_argument(
        "--out-dir",
        default="dist/final-handoff",
        help="Output root directory (default: dist/final-handoff)",
    )
    parser.add_argument(
        "--timestamp",
        default="",
        help="Override UTC timestamp suffix (default: current UTC)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent

    if args.repo:
        try:
            specs = [parse_repo_spec(value) for value in args.repo]
        except argparse.ArgumentTypeError as exc:
            parser.error(str(exc))
    else:
        specs = default_repo_specs(repo_root)

    timestamp, generated_at = utc_now()
    if args.timestamp:
        timestamp = args.timestamp

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = (repo_root / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    package_dir = out_dir / f"final-handoff-{timestamp}"
    package_dir.mkdir(parents=True, exist_ok=True)

    repos = [collect_repo_snapshot(name, path, package_dir) for name, path in specs]
    summary = summarize(repos)

    md_path = package_dir / "master-index.md"
    json_path = package_dir / "master-index.json"
    latest_md = out_dir / "final-handoff-latest.md"
    latest_json = out_dir / "final-handoff-latest.json"

    payload: dict[str, Any] = {
        "manifest_type": "cross_repo_final_handoff",
        "generated_at_utc": generated_at,
        "timestamp": timestamp,
        "read_only_collection": True,
        "package_dir_abs": str(package_dir.resolve()),
        "repos": [repo_to_dict(repo) for repo in repos],
        "summary": summary,
        "artifacts": {
            "markdown_index_abs": str(md_path.resolve()),
            "json_index_abs": str(json_path.resolve()),
            "markdown_latest_abs": str(latest_md.resolve()),
            "json_latest_abs": str(latest_json.resolve()),
        },
    }

    md_text = render_markdown(
        generated_at=generated_at,
        timestamp=timestamp,
        package_dir=package_dir,
        repos=repos,
        summary=summary,
    )

    md_path.write_text(md_text, encoding="utf-8")
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    shutil.copyfile(md_path, latest_md)
    shutil.copyfile(json_path, latest_json)

    print(f"FINAL_HANDOFF|output_dir|PASS|{package_dir.resolve()}")
    print(f"FINAL_HANDOFF|markdown|PASS|{md_path.resolve()}")
    print(f"FINAL_HANDOFF|json|PASS|{json_path.resolve()}")
    print(
        "FINAL_HANDOFF|summary|"
        f"FOUND={summary['artifacts_found']} "
        f"MISSING={summary['artifacts_missing']} "
        f"TOTAL={summary['artifacts_total']}"
    )
    if summary["artifacts_missing"] > 0:
        print("FINAL_HANDOFF|status|WARN|some expected artifacts were missing; see master indexes")
    else:
        print("FINAL_HANDOFF|status|PASS|all expected artifacts discovered")

    return 0


if __name__ == "__main__":
    sys.exit(main())
