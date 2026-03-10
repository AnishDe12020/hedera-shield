#!/usr/bin/env python3
"""Verify current repository state against latest submission freeze manifest."""

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


@dataclass
class DriftItem:
    key: str
    status: str
    expected: str
    actual: str
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


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _repo_metadata(root: Path) -> dict[str, str]:
    branch = _run_git(root, "rev-parse", "--abbrev-ref", "HEAD")
    commit = _run_git(root, "rev-parse", "HEAD")
    return {
        "branch": branch.stdout.strip() if branch.returncode == 0 else "",
        "commit_sha": commit.stdout.strip() if commit.returncode == 0 else "",
    }


def _check_repo_drift(root: Path, manifest_repo: dict[str, Any]) -> list[DriftItem]:
    current = _repo_metadata(root)
    items: list[DriftItem] = []

    expected_branch = str(manifest_repo.get("branch", ""))
    actual_branch = current.get("branch", "")
    branch_status = "PASS" if expected_branch == actual_branch else "DRIFT"
    items.append(
        DriftItem(
            key="repo_branch",
            status=branch_status,
            expected=expected_branch,
            actual=actual_branch,
            details="branch matches freeze manifest" if branch_status == "PASS" else "branch changed since freeze",
        )
    )

    expected_sha = str(manifest_repo.get("commit_sha", ""))
    actual_sha = current.get("commit_sha", "")
    sha_status = "PASS" if expected_sha == actual_sha else "DRIFT"
    items.append(
        DriftItem(
            key="repo_commit_sha",
            status=sha_status,
            expected=expected_sha,
            actual=actual_sha,
            details="commit SHA matches freeze manifest" if sha_status == "PASS" else "commit SHA changed since freeze",
        )
    )

    return items


def _check_artifact_drift(root: Path, manifest_artifacts: list[dict[str, Any]]) -> list[DriftItem]:
    items: list[DriftItem] = []
    for entry in manifest_artifacts:
        key = str(entry.get("key", "artifact"))
        expected_status = str(entry.get("status", ""))
        expected_path = str(entry.get("path", ""))
        expected_sha = str(entry.get("sha256", ""))

        if expected_status != "PASS":
            items.append(
                DriftItem(
                    key=key,
                    status="INFO",
                    expected=expected_status,
                    actual="SKIPPED",
                    details="artifact was not PASS in freeze manifest; drift check skipped",
                )
            )
            continue

        if not expected_path:
            items.append(
                DriftItem(
                    key=key,
                    status="DRIFT",
                    expected="path recorded",
                    actual="missing path",
                    details="freeze manifest PASS artifact missing path metadata",
                )
            )
            continue

        artifact_path = root / expected_path
        if not artifact_path.exists():
            items.append(
                DriftItem(
                    key=key,
                    status="DRIFT",
                    expected=expected_sha,
                    actual="MISSING",
                    details=f"missing {expected_path}",
                )
            )
            continue

        if not artifact_path.is_file():
            items.append(
                DriftItem(
                    key=key,
                    status="DRIFT",
                    expected="file",
                    actual="not-file",
                    details=f"not a file: {expected_path}",
                )
            )
            continue

        actual_sha = _sha256(artifact_path)
        status = "PASS" if actual_sha == expected_sha else "DRIFT"
        details = "checksum unchanged" if status == "PASS" else "checksum changed"
        items.append(
            DriftItem(
                key=key,
                status=status,
                expected=expected_sha,
                actual=actual_sha,
                details=details,
            )
        )

    return items


def _write_markdown(
    *,
    output_file: Path,
    timestamp_utc: str,
    generated_at_utc: str,
    manifest_path: str,
    results: list[DriftItem],
) -> None:
    pass_count = sum(1 for item in results if item.status == "PASS")
    drift_count = sum(1 for item in results if item.status == "DRIFT")
    info_count = sum(1 for item in results if item.status == "INFO")
    overall = "PASS" if drift_count == 0 else "DRIFT"

    lines: list[str] = []
    lines.append("# HederaShield Submission Freeze Drift Verification")
    lines.append("")
    lines.append(f"- Timestamp (UTC): `{timestamp_utc}`")
    lines.append(f"- Generated At (UTC): `{generated_at_utc}`")
    lines.append(f"- Manifest: `{manifest_path}`")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Overall: {overall}")
    lines.append(f"- PASS: {pass_count}")
    lines.append(f"- DRIFT: {drift_count}")
    lines.append(f"- INFO: {info_count}")
    lines.append("")
    lines.append("## Checks")
    lines.append("| Key | Status | Expected | Actual | Details |")
    lines.append("| --- | --- | --- | --- | --- |")
    for item in results:
        lines.append(
            f"| {item.key} | {item.status} | {item.expected or '-'} | {item.actual or '-'} | {item.details} |"
        )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def verify_manifest(*, root: Path, output_dir: Path, timestamp_utc: str, manifest_path: Path) -> tuple[Path, Path, list[DriftItem]]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_repo = payload.get("repo", {})
    manifest_artifacts = payload.get("artifacts", [])

    results: list[DriftItem] = []
    results.extend(_check_repo_drift(root, manifest_repo if isinstance(manifest_repo, dict) else {}))
    if isinstance(manifest_artifacts, list):
        results.extend(_check_artifact_drift(root, manifest_artifacts))
    else:
        results.append(
            DriftItem(
                key="manifest_artifacts",
                status="DRIFT",
                expected="list",
                actual=type(manifest_artifacts).__name__,
                details="manifest artifacts section is not a list",
            )
        )

    generated_at = _now_iso_utc()
    json_file = output_dir / f"drift-verify-{timestamp_utc}.json"
    md_file = output_dir / f"drift-verify-{timestamp_utc}.md"
    latest_json = output_dir / "drift-verify-latest.json"
    latest_md = output_dir / "drift-verify-latest.md"

    summary = {
        "overall": "PASS" if all(item.status != "DRIFT" for item in results) else "DRIFT",
        "pass_count": sum(1 for item in results if item.status == "PASS"),
        "drift_count": sum(1 for item in results if item.status == "DRIFT"),
        "info_count": sum(1 for item in results if item.status == "INFO"),
    }

    output = {
        "schema_version": "1.0",
        "report_type": "submission_freeze_drift_verify",
        "timestamp_utc": timestamp_utc,
        "generated_at_utc": generated_at,
        "manifest_path": str(manifest_path.relative_to(root)),
        "summary": summary,
        "checks": [asdict(item) for item in results],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    json_file.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    _write_markdown(
        output_file=md_file,
        timestamp_utc=timestamp_utc,
        generated_at_utc=generated_at,
        manifest_path=str(manifest_path.relative_to(root)),
        results=results,
    )

    shutil.copyfile(json_file, latest_json)
    shutil.copyfile(md_file, latest_md)
    return json_file, md_file, results


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="dist/submission-freeze",
        help="Output directory for drift reports (default: dist/submission-freeze)",
    )
    parser.add_argument(
        "--manifest",
        default="dist/submission-freeze/submission-freeze-latest.json",
        help="Freeze manifest JSON to verify against (default: dist/submission-freeze/submission-freeze-latest.json)",
    )
    parser.add_argument(
        "--timestamp",
        default="",
        help="Optional UTC timestamp override in format YYYYMMDDTHHMMSSZ",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    root = Path(__file__).resolve().parent.parent

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = root / output_dir

    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path

    if not manifest_path.exists():
        print(f"DRIFT|manifest|FAIL|missing {manifest_path.relative_to(root)}")
        return 2

    timestamp_utc = args.timestamp or _now_timestamp()
    json_file, md_file, results = verify_manifest(
        root=root,
        output_dir=output_dir,
        timestamp_utc=timestamp_utc,
        manifest_path=manifest_path,
    )

    for item in results:
        print(f"DRIFT|{item.key}|{item.status}|{item.details}")

    print(f"DRIFT|report_json|PASS|wrote {json_file.relative_to(root)}")
    print(f"DRIFT|report_md|PASS|wrote {md_file.relative_to(root)}")
    print("DRIFT|report_latest_json|PASS|updated dist/submission-freeze/drift-verify-latest.json")
    print("DRIFT|report_latest_md|PASS|updated dist/submission-freeze/drift-verify-latest.md")

    drift_count = sum(1 for item in results if item.status == "DRIFT")
    if drift_count == 0:
        print("DRIFT|summary|PASS|no drift detected against freeze manifest")
        return 0

    print(f"DRIFT|summary|DRIFT|detected {drift_count} drift item(s) against freeze manifest")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
