#!/usr/bin/env python3
"""Generate final portal submission packet (markdown + json) from local artifacts."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class PacketContent:
    title: str
    short_description: str
    full_description: str
    architecture: str
    innovation: str
    setup: str
    demo_steps: str
    judging_highlights: str


def _now_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _extract_section(markdown: str, heading: str) -> str:
    pattern = rf"^##\s+{re.escape(heading)}\s*$"
    matches = list(re.finditer(pattern, markdown, flags=re.MULTILINE))
    if not matches:
        return ""

    start = matches[0].end()
    next_heading = re.search(r"^##\s+", markdown[start:], flags=re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(markdown)
    return markdown[start:end].strip()


def _extract_runbook_steps(runbook_text: str) -> str:
    block = _extract_section(runbook_text, "3-Minute Script (Offline-Safe Default)")
    if not block:
        return ""

    lines = []
    for raw_line in block.splitlines():
        line = raw_line.rstrip()
        if line.startswith("### "):
            lines.append(line.replace("### ", "- ", 1))
        elif line.startswith("```bash"):
            lines.append("  Command:")
        elif line.startswith("```"):
            continue
        elif line.strip().startswith("Expected"):
            lines.append(f"  {line.strip()}")
        elif line.strip().startswith("-"):
            lines.append(f"  {line.strip()}")
        elif line.strip() and (line.strip().startswith("./") or line.strip().startswith("export") or line.strip().startswith("sha256sum") or line.strip().startswith("find ")):
            lines.append(f"  {line.strip()}")

    return "\n".join(lines).strip()


def _load_packet_content(root: Path) -> PacketContent:
    draft_pack = (root / "docs" / "SUBMISSION_FORM_DRAFT_PACK.md").read_text(encoding="utf-8")
    submission = (root / "SUBMISSION.md").read_text(encoding="utf-8")
    runbook = (root / "docs" / "DEMO_RECORDING_RUNBOOK.md").read_text(encoding="utf-8")

    problem_statement = _extract_section(draft_pack, "Problem Statement")
    solution_summary = _extract_section(draft_pack, "Solution Summary")
    architecture_short = _extract_section(draft_pack, "Architecture (Short Form)")
    innovation = _extract_section(draft_pack, "Innovation / Differentiation")
    setup = _extract_section(draft_pack, "Setup and Run Steps (Judge-Friendly)")

    hedera_integrations = _extract_section(submission, "Hedera-Specific Integrations")
    highlights = [
        "- HTS-native enforcement actions: freeze, wipe, revoke KYC.",
        "- HCS-backed immutable compliance audit trail.",
        "- Mirror Node-driven monitoring across HTS, HBAR, and NFTs.",
        "- Offline-safe deterministic demo workflow with reproducible artifacts.",
    ]
    if hedera_integrations:
        highlights.append("- Deeper integration details are documented in `SUBMISSION.md` under Hedera-Specific Integrations.")

    full_description = "\n\n".join(item for item in [problem_statement, solution_summary] if item).strip()

    return PacketContent(
        title="HederaShield: Hedera-Native AI Compliance Agent",
        short_description=(
            "AI-assisted, Hedera-native compliance monitoring and enforcement for HTS tokens "
            "with immutable HCS audit evidence."
        ),
        full_description=full_description,
        architecture=architecture_short,
        innovation=innovation,
        setup=setup,
        demo_steps=_extract_runbook_steps(runbook),
        judging_highlights="\n".join(highlights),
    )


def _git_value(root: Path, command: str) -> str:
    import subprocess

    try:
        result = subprocess.run(
            command.split(),
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return ""

    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _normalize_repo_url(repo_url: str) -> str:
    url = repo_url.strip()
    if not url:
        return ""
    if url.startswith("git@github.com:"):
        path = url.removeprefix("git@github.com:")
        if path.endswith(".git"):
            path = path[:-4]
        return f"https://github.com/{path}"
    if url.startswith("https://github.com/") and url.endswith(".git"):
        return url[:-4]
    return url


def _write_markdown(path: Path, timestamp_utc: str, packet: PacketContent, links: dict[str, str], referenced_paths: list[str]) -> None:
    lines: list[str] = []
    lines.append("# Hedera Apex Portal Submission Packet")
    lines.append("")
    lines.append(f"Generated UTC: {timestamp_utc}")
    lines.append("")
    lines.append("## Copy-Paste Fields")
    lines.append("")
    lines.append(f"- Title: {packet.title}")
    lines.append(f"- Short description: {packet.short_description}")
    lines.append("")
    lines.append("### Full description")
    lines.append(packet.full_description)
    lines.append("")
    lines.append("### Architecture")
    lines.append(packet.architecture)
    lines.append("")
    lines.append("### Innovation")
    lines.append(packet.innovation)
    lines.append("")
    lines.append("### Setup")
    lines.append(packet.setup)
    lines.append("")
    lines.append("### Demo steps")
    lines.append(packet.demo_steps)
    lines.append("")
    lines.append("### Judging highlights")
    lines.append(packet.judging_highlights)
    lines.append("")
    lines.append("## Links")
    lines.append("")
    lines.append(f"- Repository URL: {links['repo_url']}")
    lines.append(f"- Commit SHA: {links['commit_sha']}")
    lines.append(f"- Branch: {links['branch']}")
    lines.append(f"- Demo video URL: {links['demo_video_url']}")
    lines.append(f"- Deployed URL: {links['deployed_url']}")
    lines.append(f"- Demo report markdown: `{links['demo_report_md']}`")
    lines.append(f"- Demo report json: `{links['demo_report_json']}`")
    lines.append(f"- Submission bundle: `{links['submission_bundle']}`")
    lines.append(f"- Release evidence bundle: `{links['release_evidence_bundle']}`")
    lines.append("")
    lines.append("## Referenced Paths")
    lines.append("")
    for rel in referenced_paths:
        lines.append(f"- `{rel}`")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(root: Path, output_dir: Path, timestamp_utc: str) -> tuple[Path, Path]:
    packet = _load_packet_content(root)

    release_bundles = sorted((root / "dist").glob("release-evidence-*.tar.gz"))
    latest_release_bundle = str(release_bundles[-1].relative_to(root)) if release_bundles else ""

    repo_url = _normalize_repo_url(_git_value(root, "git config --get remote.origin.url"))
    commit_sha = _git_value(root, "git rev-parse HEAD")
    branch = _git_value(root, "git rev-parse --abbrev-ref HEAD")

    links = {
        "repo_url": repo_url or "local-only-repository",
        "commit_sha": commit_sha or "unknown",
        "branch": branch or "unknown",
        "demo_video_url": "TODO_ADD_DEMO_VIDEO_URL",
        "deployed_url": "TODO_ADD_FINAL_DEPLOYED_URL_OR_NA",
        "demo_report_md": "artifacts/demo/3min-offline/harness/report.md",
        "demo_report_json": "artifacts/demo/3min-offline/harness/report.json",
        "submission_bundle": "dist/submission-bundle.zip",
        "release_evidence_bundle": latest_release_bundle or "dist/release-evidence-<timestamp>.tar.gz",
    }

    referenced_paths = [
        "README.md",
        "SUBMISSION.md",
        "docs/SUBMISSION_FORM_DRAFT_PACK.md",
        "docs/DEMO_RECORDING_RUNBOOK.md",
        "docs/DEMO_NARRATION_3MIN.md",
        "docs/FINAL_SUBMISSION_CHECKLIST.md",
        "docs/TESTNET_SETUP.md",
        "docs/TESTNET_EVIDENCE.md",
        "docs/DEPLOY_PROOF.md",
        "artifacts/demo/3min-offline/harness/report.md",
        "artifacts/demo/3min-offline/harness/report.json",
        "dist/submission-bundle.zip",
    ]
    if latest_release_bundle:
        referenced_paths.append(latest_release_bundle)

    timestamp_dir = output_dir / timestamp_utc
    md_path = timestamp_dir / "portal-submission-packet.md"
    json_path = timestamp_dir / "portal-submission-packet.json"

    _write_markdown(md_path, timestamp_utc, packet, links, referenced_paths)

    payload = {
        "manifest_type": "hedera_apex_portal_submission_packet",
        "generated_at_utc": timestamp_utc,
        "fields": {
            "title": packet.title,
            "short_description": packet.short_description,
            "full_description": packet.full_description,
            "architecture": packet.architecture,
            "innovation": packet.innovation,
            "setup": packet.setup,
            "demo_steps": packet.demo_steps,
            "judging_highlights": packet.judging_highlights,
        },
        "links": links,
        "referenced_paths": referenced_paths,
        "sources": [
            "SUBMISSION.md",
            "docs/SUBMISSION_FORM_DRAFT_PACK.md",
            "docs/DEMO_RECORDING_RUNBOOK.md",
            "docs/FINAL_SUBMISSION_CHECKLIST.md",
        ],
    }
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    latest_md = output_dir / "portal-submission-packet-latest.md"
    latest_json = output_dir / "portal-submission-packet-latest.json"
    shutil.copyfile(md_path, latest_md)
    shutil.copyfile(json_path, latest_json)

    print(f"PORTAL_PACKET|markdown|PASS|wrote {md_path.relative_to(root)}")
    print(f"PORTAL_PACKET|json|PASS|wrote {json_path.relative_to(root)}")
    print("PORTAL_PACKET|latest|PASS|updated dist/portal-submission/portal-submission-packet-latest.md")
    print("PORTAL_PACKET|latest_json|PASS|updated dist/portal-submission/portal-submission-packet-latest.json")

    return md_path, json_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timestamp", default="", help="Optional UTC timestamp (YYYYMMDDTHHMMSSZ)")
    parser.add_argument(
        "--output-dir",
        default="dist/portal-submission",
        help="Output directory for packet files (default: dist/portal-submission)",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    root = Path(__file__).resolve().parent.parent
    timestamp_utc = args.timestamp or _now_timestamp()

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = root / output_dir

    run(root=root, output_dir=output_dir, timestamp_utc=timestamp_utc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
