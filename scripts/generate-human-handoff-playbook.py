#!/usr/bin/env python3
"""Generate execution-ready human handoff playbook (markdown + json)."""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class ArtifactStatus:
    key: str
    label: str
    required: bool
    status: str
    details: str
    absolute_path: str


@dataclass
class Blocker:
    key: str
    title: str
    status: str
    details: str
    resolution: str


@dataclass
class PlanStep:
    key: str
    title: str
    status: str
    owner: str
    objective: str
    checklist: list[str]
    commands: list[str]
    required_paths: list[str]


def _now_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _is_placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    if not lowered:
        return True
    if lowered in {"na", "n/a", "none", "unknown", "unset"}:
        return True
    placeholders = ["todo", "paste", "fill", "<", "local-only-repository"]
    return any(token in lowered for token in placeholders)


def _path_status(root: Path, key: str, label: str, rel_path: str, required: bool = True) -> ArtifactStatus:
    abs_path = (root / rel_path).resolve()
    if abs_path.exists():
        return ArtifactStatus(
            key=key,
            label=label,
            required=required,
            status="PASS",
            details=f"found {abs_path}",
            absolute_path=str(abs_path),
        )

    return ArtifactStatus(
        key=key,
        label=label,
        required=required,
        status="FAIL" if required else "WARN",
        details=f"missing {abs_path}",
        absolute_path=str(abs_path),
    )


def _latest_match(root: Path, pattern: str) -> Path | None:
    matches = sorted(root.glob(pattern))
    if not matches:
        return None
    return matches[-1]


def _load_packet_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _collect_artifacts(root: Path) -> tuple[list[ArtifactStatus], dict[str, str]]:
    statuses = [
        _path_status(root, "demo_runbook", "Demo recording runbook", "docs/DEMO_RECORDING_RUNBOOK.md"),
        _path_status(root, "demo_narration", "Demo narration script", "docs/DEMO_NARRATION_3MIN.md"),
        _path_status(root, "form_draft", "Submission form draft pack", "docs/SUBMISSION_FORM_DRAFT_PACK.md"),
        _path_status(root, "final_checklist", "Final submission checklist", "docs/FINAL_SUBMISSION_CHECKLIST.md"),
        _path_status(root, "demo_report_md", "Offline demo harness report (markdown)", "artifacts/demo/3min-offline/harness/report.md"),
        _path_status(root, "demo_report_json", "Offline demo harness report (json)", "artifacts/demo/3min-offline/harness/report.json"),
        _path_status(root, "bundle_sha", "Submission bundle checksum", "artifacts/demo/3min-offline/submission-bundle.zip.sha256"),
        _path_status(root, "bundle_zip", "Submission bundle zip", "dist/submission-bundle.zip"),
        _path_status(root, "packet_md", "Portal packet markdown", "dist/portal-submission/portal-submission-packet-latest.md"),
        _path_status(root, "packet_json", "Portal packet json", "dist/portal-submission/portal-submission-packet-latest.json"),
        _path_status(root, "readiness_report", "Submission readiness report", "dist/submission-readiness-latest.txt"),
        _path_status(root, "pre_submit_verify", "Pre-submit verify report", "dist/pre-submit-verify-latest.txt"),
        _path_status(root, "freeze_manifest", "Submission freeze manifest", "dist/submission-freeze/submission-freeze-latest.json", required=False),
        _path_status(root, "drift_verify", "Submission drift verify", "dist/submission-freeze/drift-verify-latest.json", required=False),
    ]

    latest_release = _latest_match(root / "dist", "release-evidence-*.tar.gz")
    if latest_release is not None:
        statuses.append(
            ArtifactStatus(
                key="release_bundle",
                label="Release evidence tarball",
                required=False,
                status="PASS",
                details=f"found {latest_release.resolve()}",
                absolute_path=str(latest_release.resolve()),
            )
        )
    else:
        statuses.append(
            ArtifactStatus(
                key="release_bundle",
                label="Release evidence tarball",
                required=False,
                status="WARN",
                details=f"missing {(root / 'dist' / 'release-evidence-*.tar.gz').resolve()}",
                absolute_path=str((root / "dist" / "release-evidence-*.tar.gz").resolve()),
            )
        )

    by_key = {item.key: item.absolute_path for item in statuses}
    return statuses, by_key


def _build_blockers(
    artifacts: list[ArtifactStatus],
    packet: dict[str, Any],
    demo_video_url: str,
    portal_submission_url: str,
) -> list[Blocker]:
    blockers: list[Blocker] = []

    missing_required = [item for item in artifacts if item.required and item.status != "PASS"]
    if missing_required:
        blockers.append(
            Blocker(
                key="missing_required_artifacts",
                title="Required artifacts are missing",
                status="OPEN",
                details="; ".join(item.details for item in missing_required),
                resolution="Run release/readiness generators until all required artifacts pass.",
            )
        )

    if _is_placeholder(demo_video_url):
        blockers.append(
            Blocker(
                key="missing_demo_video_url",
                title="Demo video URL is not set",
                status="OPEN",
                details="Demo video URL is still placeholder/empty.",
                resolution="Record + upload demo video, then rerun with --demo-video-url <public-or-unlisted-url>.",
            )
        )

    links = packet.get("links", {}) if isinstance(packet, dict) else {}
    repo_url = str(links.get("repo_url", "")).strip()
    commit_sha = str(links.get("commit_sha", "")).strip()

    if _is_placeholder(repo_url):
        blockers.append(
            Blocker(
                key="missing_repo_url",
                title="Repository URL in packet is placeholder",
                status="OPEN",
                details="Portal packet repo URL is missing or placeholder.",
                resolution="Regenerate portal packet from a repo with remote.origin.url set.",
            )
        )

    if _is_placeholder(commit_sha):
        blockers.append(
            Blocker(
                key="missing_commit_sha",
                title="Commit SHA in packet is placeholder",
                status="OPEN",
                details="Portal packet commit SHA is missing or placeholder.",
                resolution="Commit current state and regenerate portal packet.",
            )
        )

    if _is_placeholder(portal_submission_url):
        blockers.append(
            Blocker(
                key="missing_portal_submission_url",
                title="Portal submission URL is not set",
                status="OPEN",
                details="Portal submission URL for proof capture is empty/placeholder.",
                resolution="Set --portal-submission-url once final portal form is open.",
            )
        )

    return blockers


def _build_steps(root: Path, paths: dict[str, str], blockers: list[Blocker], demo_video_url: str, portal_submission_url: str) -> list[PlanStep]:
    missing_artifact_blocker = any(item.key == "missing_required_artifacts" for item in blockers)
    missing_demo_url_blocker = any(item.key == "missing_demo_video_url" for item in blockers)
    missing_portal_url_blocker = any(item.key == "missing_portal_submission_url" for item in blockers)

    step1_status = "BLOCKED" if missing_artifact_blocker else ("PENDING" if missing_demo_url_blocker else "DONE")
    step2_status = "BLOCKED" if missing_artifact_blocker else "PENDING"
    step3_status = "BLOCKED" if missing_artifact_blocker or missing_demo_url_blocker or missing_portal_url_blocker else "PENDING"

    return [
        PlanStep(
            key="record_demo",
            title="Record and Upload Final Demo",
            status=step1_status,
            owner="Anish",
            objective="Produce final demo video and capture public/unlisted URL.",
            checklist=[
                "Open runbook and narration side-by-side.",
                "Record 3-minute walkthrough using offline-safe evidence flow.",
                "Upload video and store URL in notes.",
                f"Re-run generator with --demo-video-url once uploaded (current: {demo_video_url or 'unset'}).",
            ],
            commands=[
                f"cat '{paths.get('demo_runbook', str((root / 'docs/DEMO_RECORDING_RUNBOOK.md').resolve()))}'",
                f"cat '{paths.get('demo_narration', str((root / 'docs/DEMO_NARRATION_3MIN.md').resolve()))}'",
                "./scripts/submission-readiness.sh",
            ],
            required_paths=[
                paths.get("demo_runbook", str((root / "docs/DEMO_RECORDING_RUNBOOK.md").resolve())),
                paths.get("demo_narration", str((root / "docs/DEMO_NARRATION_3MIN.md").resolve())),
                paths.get("demo_report_md", str((root / "artifacts/demo/3min-offline/harness/report.md").resolve())),
                paths.get("demo_report_json", str((root / "artifacts/demo/3min-offline/harness/report.json").resolve())),
            ],
        ),
        PlanStep(
            key="fill_portal_form",
            title="Fill Hackathon Portal Form",
            status=step2_status,
            owner="Anish",
            objective="Copy finalized technical content and evidence links into portal fields.",
            checklist=[
                "Open latest portal submission packet markdown.",
                "Paste title/description/architecture/innovation/setup fields.",
                "Paste repository URL and commit SHA from packet.",
                "Paste demo video URL and bundle evidence details.",
            ],
            commands=[
                "./scripts/generate-portal-submission-packet.py",
                "./scripts/verify-portal-submission-packet.py",
                f"cat '{paths.get('packet_md', str((root / 'dist/portal-submission/portal-submission-packet-latest.md').resolve()))}'",
            ],
            required_paths=[
                paths.get("packet_md", str((root / "dist/portal-submission/portal-submission-packet-latest.md").resolve())),
                paths.get("packet_json", str((root / "dist/portal-submission/portal-submission-packet-latest.json").resolve())),
                paths.get("form_draft", str((root / "docs/SUBMISSION_FORM_DRAFT_PACK.md").resolve())),
                paths.get("bundle_zip", str((root / "dist/submission-bundle.zip").resolve())),
                paths.get("bundle_sha", str((root / "artifacts/demo/3min-offline/submission-bundle.zip.sha256").resolve())),
            ],
        ),
        PlanStep(
            key="final_submit",
            title="Final Portal Submit and Proof Capture",
            status=step3_status,
            owner="Anish",
            objective="Submit final entry and preserve submission proof + push state.",
            checklist=[
                f"Open portal URL and submit final form (current: {portal_submission_url or 'unset'}).",
                "Capture confirmation page screenshot and URL.",
                "Run sync/push best-effort and store status artifact if push fails.",
                "Regenerate this handoff playbook for final state snapshot.",
            ],
            commands=[
                "./scripts/sync-and-submit.sh --max-retries 3 --initial-backoff-seconds 2 --max-backoff-seconds 16",
                "./scripts/network-recovery-push-runner.sh --check-interval-seconds 30 --max-checks 20",
                "./scripts/generate-human-handoff-playbook.py",
            ],
            required_paths=[
                paths.get("final_checklist", str((root / "docs/FINAL_SUBMISSION_CHECKLIST.md").resolve())),
                paths.get("readiness_report", str((root / "dist/submission-readiness-latest.txt").resolve())),
                paths.get("pre_submit_verify", str((root / "dist/pre-submit-verify-latest.txt").resolve())),
            ],
        ),
    ]


def _write_markdown(
    md_path: Path,
    *,
    timestamp_utc: str,
    root: Path,
    artifacts: list[ArtifactStatus],
    blockers: list[Blocker],
    steps: list[PlanStep],
    demo_video_url: str,
    portal_submission_url: str,
) -> None:
    total_required = sum(1 for item in artifacts if item.required)
    required_pass = sum(1 for item in artifacts if item.required and item.status == "PASS")
    readiness = "READY" if not blockers else "BLOCKED"

    lines: list[str] = []
    lines.append("# HederaShield Human Handoff Playbook")
    lines.append("")
    lines.append(f"Generated UTC: {timestamp_utc}")
    lines.append(f"Workspace: {root}")
    lines.append(f"Readiness Gate: **{readiness}**")
    lines.append("")
    lines.append("## Gate Summary")
    lines.append("")
    lines.append(f"- Required artifacts complete: {required_pass}/{total_required}")
    lines.append(f"- Open blockers: {len(blockers)}")
    lines.append(f"- Demo video URL: {demo_video_url or 'UNSET'}")
    lines.append(f"- Portal submission URL: {portal_submission_url or 'UNSET'}")
    lines.append("")

    lines.append("## Blockers")
    lines.append("")
    if blockers:
        for blocker in blockers:
            lines.append(f"- [ ] {blocker.title} ({blocker.key})")
            lines.append(f"  - Details: {blocker.details}")
            lines.append(f"  - Resolution: {blocker.resolution}")
    else:
        lines.append("- [x] No open blockers.")
    lines.append("")

    lines.append("## Completed Checks")
    lines.append("")
    for item in artifacts:
        checkbox = "[x]" if item.status == "PASS" else "[ ]"
        lines.append(f"- {checkbox} {item.label} ({item.status})")
        lines.append(f"  - Path: {item.absolute_path}")
        lines.append(f"  - Details: {item.details}")
    lines.append("")

    lines.append("## Execution Plan")
    lines.append("")
    for index, step in enumerate(steps, start=1):
        lines.append(f"### Step {index}: {step.title}")
        lines.append(f"Status: **{step.status}**")
        lines.append(f"Owner: {step.owner}")
        lines.append(f"Objective: {step.objective}")
        lines.append("")
        lines.append("Checklist:")
        for item in step.checklist:
            lines.append(f"- [ ] {item}")
        lines.append("")
        lines.append("Commands:")
        lines.append("```bash")
        for cmd in step.commands:
            lines.append(cmd)
        lines.append("```")
        lines.append("")
        lines.append("Required absolute paths:")
        for path in step.required_paths:
            lines.append(f"- {path}")
        lines.append("")

    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def run(root: Path, output_dir: Path, timestamp_utc: str, demo_video_url: str, portal_submission_url: str) -> tuple[Path, Path, dict[str, Any]]:
    artifacts, paths_by_key = _collect_artifacts(root)

    packet_json_path = root / "dist" / "portal-submission" / "portal-submission-packet-latest.json"
    packet = _load_packet_json(packet_json_path)
    packet_links = packet.get("links", {}) if isinstance(packet, dict) else {}

    effective_demo_video_url = demo_video_url.strip() if demo_video_url.strip() else str(packet_links.get("demo_video_url", "")).strip()
    effective_portal_submission_url = portal_submission_url.strip()

    blockers = _build_blockers(
        artifacts=artifacts,
        packet=packet,
        demo_video_url=effective_demo_video_url,
        portal_submission_url=effective_portal_submission_url,
    )
    steps = _build_steps(
        root=root,
        paths=paths_by_key,
        blockers=blockers,
        demo_video_url=effective_demo_video_url,
        portal_submission_url=effective_portal_submission_url,
    )

    out_dir = output_dir / timestamp_utc
    md_path = out_dir / "human-handoff-playbook.md"
    json_path = out_dir / "human-handoff-playbook.json"

    _write_markdown(
        md_path,
        timestamp_utc=timestamp_utc,
        root=root,
        artifacts=artifacts,
        blockers=blockers,
        steps=steps,
        demo_video_url=effective_demo_video_url,
        portal_submission_url=effective_portal_submission_url,
    )

    payload = {
        "manifest_type": "human_handoff_playbook",
        "generated_at_utc": timestamp_utc,
        "workspace_root": str(root.resolve()),
        "readiness": {
            "status": "READY" if not blockers else "BLOCKED",
            "required_total": sum(1 for item in artifacts if item.required),
            "required_pass": sum(1 for item in artifacts if item.required and item.status == "PASS"),
            "open_blockers": len(blockers),
        },
        "inputs": {
            "demo_video_url": effective_demo_video_url,
            "portal_submission_url": effective_portal_submission_url,
        },
        "artifact_status": [asdict(item) for item in artifacts],
        "blockers": [asdict(item) for item in blockers],
        "steps": [asdict(item) for item in steps],
    }

    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    latest_md = output_dir / "human-handoff-playbook-latest.md"
    latest_json = output_dir / "human-handoff-playbook-latest.json"
    shutil.copyfile(md_path, latest_md)
    shutil.copyfile(json_path, latest_json)

    print(f"HANDOFF_PLAYBOOK|markdown|PASS|wrote {md_path.relative_to(root)}")
    print(f"HANDOFF_PLAYBOOK|json|PASS|wrote {json_path.relative_to(root)}")
    print("HANDOFF_PLAYBOOK|latest_md|PASS|updated dist/handoff-playbook/human-handoff-playbook-latest.md")
    print("HANDOFF_PLAYBOOK|latest_json|PASS|updated dist/handoff-playbook/human-handoff-playbook-latest.json")
    print(
        "HANDOFF_PLAYBOOK|summary|{}|required={}/{} blockers={}".format(
            payload["readiness"]["status"],
            payload["readiness"]["required_pass"],
            payload["readiness"]["required_total"],
            payload["readiness"]["open_blockers"],
        )
    )

    return md_path, json_path, payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timestamp", default="", help="Optional UTC timestamp (YYYYMMDDTHHMMSSZ)")
    parser.add_argument(
        "--output-dir",
        default="dist/handoff-playbook",
        help="Output directory (default: dist/handoff-playbook)",
    )
    parser.add_argument(
        "--demo-video-url",
        default="",
        help="Final uploaded demo video URL. If omitted, uses packet value if available.",
    )
    parser.add_argument(
        "--portal-submission-url",
        default="",
        help="Hackathon portal submission URL for proof capture.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    root = Path(__file__).resolve().parent.parent
    timestamp_utc = args.timestamp or _now_timestamp()

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = root / output_dir

    run(
        root=root,
        output_dir=output_dir,
        timestamp_utc=timestamp_utc,
        demo_video_url=args.demo_video_url,
        portal_submission_url=args.portal_submission_url,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
