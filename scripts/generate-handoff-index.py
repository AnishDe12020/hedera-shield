#!/usr/bin/env python3
"""Generate a judge handoff index linking latest evidence artifacts."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class ItemStatus:
    key: str
    label: str
    required: bool
    status: str
    details: str
    path: str | None
    action: str | None


def _now_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _latest_match(root: Path, pattern: str) -> Path | None:
    matches = sorted(root.glob(pattern))
    if not matches:
        return None
    return matches[-1]


def _latest_dir(root: Path, pattern: str) -> Path | None:
    matches = [path for path in sorted(root.glob(pattern)) if path.is_dir()]
    if not matches:
        return None
    return matches[-1]


def _rel(root: Path, path: Path) -> str:
    return str(path.resolve().relative_to(root.resolve()))


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


def _item(
    items: list[ItemStatus],
    *,
    key: str,
    label: str,
    required: bool,
    path: Path | None,
    details_if_missing: str,
    action: str | None,
    root: Path,
) -> None:
    if path is not None and path.exists():
        items.append(
            ItemStatus(
                key=key,
                label=label,
                required=required,
                status="PASS",
                details=f"found {_rel(root, path)}",
                path=_rel(root, path),
                action=None,
            )
        )
        return

    status = "FAIL" if required else "WARN"
    items.append(
        ItemStatus(
            key=key,
            label=label,
            required=required,
            status=status,
            details=details_if_missing,
            path=None,
            action=action,
        )
    )


def _build_items(root: Path) -> tuple[list[ItemStatus], dict[str, str], dict[str, str]]:
    items: list[ItemStatus] = []
    latest: dict[str, str] = {}

    release_bundle = _latest_match(root / "dist", "release-evidence-*.tar.gz")
    _item(
        items,
        key="release_bundle_latest",
        label="Latest release-evidence bundle",
        required=False,
        path=release_bundle,
        details_if_missing="missing dist/release-evidence-*.tar.gz",
        action="./scripts/release-evidence.sh",
        root=root,
    )
    if release_bundle is not None and release_bundle.exists():
        latest["release_bundle_latest"] = _rel(root, release_bundle)

    integration_release = _latest_dir(root / "artifacts" / "integration", "release-*")
    _item(
        items,
        key="integration_release_dir_latest",
        label="Latest integration release directory",
        required=False,
        path=integration_release,
        details_if_missing="missing artifacts/integration/release-*",
        action="./scripts/release-evidence.sh",
        root=root,
    )
    if integration_release is not None and integration_release.exists():
        latest["integration_release_dir_latest"] = _rel(root, integration_release)

    release_report_md = integration_release / "release-report.md" if integration_release else None
    release_report_json = integration_release / "release-report.json" if integration_release else None
    mock_report_md = integration_release / "mock" / "report.md" if integration_release else None
    mock_report_json = integration_release / "mock" / "report.json" if integration_release else None

    _item(
        items,
        key="integration_release_report_md",
        label="Integration release report (markdown)",
        required=False,
        path=release_report_md,
        details_if_missing="missing artifacts/integration/release-*/release-report.md",
        action="./scripts/release-evidence.sh",
        root=root,
    )
    _item(
        items,
        key="integration_release_report_json",
        label="Integration release report (json)",
        required=False,
        path=release_report_json,
        details_if_missing="missing artifacts/integration/release-*/release-report.json",
        action="./scripts/release-evidence.sh",
        root=root,
    )
    _item(
        items,
        key="integration_mock_report_md",
        label="Mock integration report (markdown)",
        required=False,
        path=mock_report_md,
        details_if_missing="missing artifacts/integration/release-*/mock/report.md",
        action=(
            "./scripts/run-integration-harness.sh --mode mock "
            "--env-file .env.testnet.example "
            "--artifacts-dir artifacts/integration/release-<timestamp>/mock"
        ),
        root=root,
    )
    _item(
        items,
        key="integration_mock_report_json",
        label="Mock integration report (json)",
        required=False,
        path=mock_report_json,
        details_if_missing="missing artifacts/integration/release-*/mock/report.json",
        action=(
            "./scripts/run-integration-harness.sh --mode mock "
            "--env-file .env.testnet.example "
            "--artifacts-dir artifacts/integration/release-<timestamp>/mock"
        ),
        root=root,
    )

    offline_handoff = _latest_dir(root / "artifacts" / "offline-handoff", "*")
    _item(
        items,
        key="offline_handoff_dir_latest",
        label="Latest offline-handoff package directory",
        required=False,
        path=offline_handoff,
        details_if_missing="missing artifacts/offline-handoff/<timestamp>/",
        action="./scripts/offline-handoff.sh",
        root=root,
    )
    if offline_handoff is not None and offline_handoff.exists():
        latest["offline_handoff_dir_latest"] = _rel(root, offline_handoff)

    offline_summary = offline_handoff / "handoff-summary.txt" if offline_handoff else None
    offline_bundle = offline_handoff / "offline.bundle" if offline_handoff else None
    offline_restore = offline_handoff / "RESTORE_APPLY.md" if offline_handoff else None

    _item(
        items,
        key="offline_handoff_summary",
        label="Offline handoff summary",
        required=False,
        path=offline_summary,
        details_if_missing="missing artifacts/offline-handoff/<timestamp>/handoff-summary.txt",
        action="./scripts/offline-handoff.sh",
        root=root,
    )
    _item(
        items,
        key="offline_handoff_bundle",
        label="Offline handoff git bundle",
        required=False,
        path=offline_bundle,
        details_if_missing="missing artifacts/offline-handoff/<timestamp>/offline.bundle",
        action="./scripts/offline-handoff.sh",
        root=root,
    )
    _item(
        items,
        key="offline_handoff_restore",
        label="Offline restore/apply instructions",
        required=False,
        path=offline_restore,
        details_if_missing="missing artifacts/offline-handoff/<timestamp>/RESTORE_APPLY.md",
        action="./scripts/offline-handoff.sh",
        root=root,
    )

    demo_runbook = root / "docs" / "DEMO_RECORDING_RUNBOOK.md"
    final_checklist = root / "docs" / "FINAL_SUBMISSION_CHECKLIST.md"

    _item(
        items,
        key="demo_runbook",
        label="Demo checklist/runbook",
        required=True,
        path=demo_runbook,
        details_if_missing="missing docs/DEMO_RECORDING_RUNBOOK.md",
        action="restore docs/DEMO_RECORDING_RUNBOOK.md",
        root=root,
    )
    _item(
        items,
        key="final_submission_checklist",
        label="Final submission checklist",
        required=True,
        path=final_checklist,
        details_if_missing="missing docs/FINAL_SUBMISSION_CHECKLIST.md",
        action="restore docs/FINAL_SUBMISSION_CHECKLIST.md",
        root=root,
    )

    readiness_report = root / "dist" / "submission-readiness-latest.txt"
    _item(
        items,
        key="submission_readiness_latest",
        label="Submission readiness latest report",
        required=False,
        path=readiness_report,
        details_if_missing="missing dist/submission-readiness-latest.txt",
        action="./scripts/submission-readiness.sh",
        root=root,
    )

    sync_report = root / "dist" / "sync-submit-status-latest.txt"
    _item(
        items,
        key="sync_submit_latest",
        label="Sync/submit latest report",
        required=False,
        path=sync_report,
        details_if_missing="missing dist/sync-submit-status-latest.txt",
        action=(
            "./scripts/sync-and-submit.sh --max-retries 3 "
            "--initial-backoff-seconds 2 --max-backoff-seconds 16"
        ),
        root=root,
    )

    push_report = root / "dist" / "git-push-status-latest.txt"
    _item(
        items,
        key="git_push_status_latest",
        label="Direct git push latest report",
        required=False,
        path=push_report,
        details_if_missing="missing dist/git-push-status-latest.txt",
        action="git push origin <branch> > dist/git-push-status-latest.txt 2>&1",
        root=root,
    )

    sync_context: dict[str, str] = {}
    if sync_report.exists():
        sync_text = sync_report.read_text(encoding="utf-8", errors="replace")
        reachability_error = _extract_named_block(sync_text, "REMOTE_REACHABILITY_ERROR:")
        push_error = _extract_named_block(sync_text, "PUSH_FINAL_ERROR:")
        if reachability_error:
            sync_context["remote_reachability_error"] = reachability_error
        if push_error:
            sync_context["push_final_error"] = push_error

    if push_report.exists():
        push_text = push_report.read_text(encoding="utf-8", errors="replace").strip()
        if push_text:
            sync_context["git_push_error"] = push_text

    return items, latest, sync_context


def _summary(items: list[ItemStatus]) -> dict[str, Any]:
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for item in items:
        counts[item.status] = counts.get(item.status, 0) + 1

    overall = "READY"
    if counts["FAIL"] > 0 or counts["WARN"] > 0:
        overall = "ACTION_NEEDED"

    return {
        "overall": overall,
        "pass": counts["PASS"],
        "warn": counts["WARN"],
        "fail": counts["FAIL"],
        "total": len(items),
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# HederaShield Judge Handoff Index")
    lines.append("")
    lines.append(f"- Timestamp (UTC): `{payload['timestamp_utc']}`")
    lines.append(f"- Generated at (UTC): `{payload['generated_at_utc']}`")
    lines.append(f"- Overall status: `{payload['summary']['overall']}`")
    lines.append(
        "- Summary counts: "
        f"PASS={payload['summary']['pass']} "
        f"WARN={payload['summary']['warn']} "
        f"FAIL={payload['summary']['fail']}"
    )
    lines.append("")
    lines.append("## Key Links")

    latest = payload["latest_paths"]
    for key in (
        "release_bundle_latest",
        "integration_release_dir_latest",
        "offline_handoff_dir_latest",
    ):
        if key in latest:
            lines.append(f"- `{key}`: `{latest[key]}`")

    for key in ("demo_runbook", "final_submission_checklist"):
        match = next(item for item in payload["items"] if item["key"] == key)
        if match["path"]:
            lines.append(f"- `{match['key']}`: `{match['path']}`")

    lines.append("")
    lines.append("## Artifact Status")
    lines.append("| Key | Required | Status | Path | Details |")
    lines.append("|---|---|---|---|---|")
    for item in payload["items"]:
        lines.append(
            "| "
            f"`{item['key']}` | "
            f"`{'yes' if item['required'] else 'no'}` | "
            f"`{item['status']}` | "
            f"`{item['path'] or '-'}` | "
            f"{item['details']} |"
        )

    action_items = [item for item in payload["items"] if item["status"] != "PASS" and item["action"]]
    if action_items:
        lines.append("")
        lines.append("## Actionable Next Commands")
        for item in action_items:
            lines.append(f"- `{item['key']}`: `{item['action']}`")

    sync_context = payload.get("sync_context", {})
    if sync_context:
        lines.append("")
        lines.append("## Sync/Push Error Context")
        if "remote_reachability_error" in sync_context:
            lines.append("### REMOTE_REACHABILITY_ERROR")
            lines.append("```text")
            lines.append(sync_context["remote_reachability_error"])
            lines.append("```")
        if "push_final_error" in sync_context:
            lines.append("### PUSH_FINAL_ERROR")
            lines.append("```text")
            lines.append(sync_context["push_final_error"])
            lines.append("```")
        if "git_push_error" in sync_context:
            lines.append("### GIT_PUSH_ERROR")
            lines.append("```text")
            lines.append(sync_context["git_push_error"])
            lines.append("```")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a judge handoff index (markdown + json)")
    parser.add_argument("--timestamp", default=_now_timestamp(), help="UTC timestamp in YYYYMMDDTHHMMSSZ")
    parser.add_argument("--output-base-dir", default="artifacts/handoff-index")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    output_dir = (root / args.output_base_dir / args.timestamp).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    items, latest_paths, sync_context = _build_items(root)
    payload: dict[str, Any] = {
        "timestamp_utc": args.timestamp,
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "output_dir": _rel(root, output_dir),
        "latest_paths": latest_paths,
        "summary": _summary(items),
        "items": [asdict(item) for item in items],
    }
    if sync_context:
        payload["sync_context"] = sync_context

    md_path = output_dir / "handoff-index.md"
    json_path = output_dir / "handoff-index.json"

    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(_render_markdown(payload), encoding="utf-8")

    print(f"HANDOFF_INDEX|output_dir|PASS|{_rel(root, output_dir)}")
    print(f"HANDOFF_INDEX|markdown|PASS|{_rel(root, md_path)}")
    print(f"HANDOFF_INDEX|json|PASS|{_rel(root, json_path)}")
    print(
        "HANDOFF_INDEX|summary|"
        f"{payload['summary']['overall']}|"
        f"PASS={payload['summary']['pass']} WARN={payload['summary']['warn']} FAIL={payload['summary']['fail']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
