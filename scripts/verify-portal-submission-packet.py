#!/usr/bin/env python3
"""Verify all paths referenced by portal submission packet manifest exist."""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class CheckResult:
    key: str
    status: str
    details: str


def _now_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _rel(root: Path, path: Path) -> str:
    return str(path.resolve().relative_to(root.resolve()))


def _write_report(root: Path, report_file: Path, results: list[CheckResult], timestamp_utc: str) -> None:
    pass_count = sum(1 for item in results if item.status == "PASS")
    fail_count = sum(1 for item in results if item.status == "FAIL")
    overall = "PASS" if fail_count == 0 else "FAIL"

    lines = [
        "HederaShield Portal Submission Packet Verify",
        f"Timestamp UTC: {timestamp_utc}",
        "",
        "Summary",
        f"- Overall: {overall}",
        f"- PASS: {pass_count}",
        f"- FAIL: {fail_count}",
        "",
        "Checks",
    ]
    lines.extend(f"PORTAL_VERIFY|{item.key}|{item.status}|{item.details}" for item in results)

    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    latest_txt = root / "dist" / "portal-submission" / "portal-submission-verify-latest.txt"
    latest_txt.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(report_file, latest_txt)

    latest_json = root / "dist" / "portal-submission" / "portal-submission-verify-latest.json"
    report_payload = {
        "manifest_type": "portal_submission_packet_verify",
        "generated_at_utc": timestamp_utc,
        "overall": overall,
        "pass": pass_count,
        "fail": fail_count,
        "checks": [item.__dict__ for item in results],
    }
    latest_json.write_text(json.dumps(report_payload, indent=2) + "\n", encoding="utf-8")


def run(root: Path, packet_json: Path, report_file: Path) -> int:
    if not packet_json.exists():
        print(f"PORTAL_VERIFY|packet_manifest|FAIL|missing {_rel(root, packet_json)}")
        results = [CheckResult("packet_manifest", "FAIL", f"missing {_rel(root, packet_json)}")]
        _write_report(root, report_file, results, _now_timestamp())
        return 1

    try:
        payload = json.loads(packet_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        details = f"invalid json in {_rel(root, packet_json)}: {exc}"
        print(f"PORTAL_VERIFY|packet_manifest|FAIL|{details}")
        results = [CheckResult("packet_manifest", "FAIL", details)]
        _write_report(root, report_file, results, _now_timestamp())
        return 1

    results: list[CheckResult] = []
    referenced_paths = payload.get("referenced_paths", [])
    if not isinstance(referenced_paths, list) or not referenced_paths:
        results.append(CheckResult("referenced_paths", "FAIL", "missing or empty referenced_paths list"))
    else:
        results.append(CheckResult("referenced_paths", "PASS", f"loaded {len(referenced_paths)} referenced paths"))
        for index, rel_path in enumerate(referenced_paths, start=1):
            key = f"path_{index:02d}"
            if not isinstance(rel_path, str) or not rel_path.strip():
                results.append(CheckResult(key, "FAIL", "invalid empty path entry"))
                continue
            path = root / rel_path
            if path.exists():
                details = f"found {rel_path}"
                results.append(CheckResult(key, "PASS", details))
            else:
                details = f"missing {rel_path}"
                results.append(CheckResult(key, "FAIL", details))

    fail_count = sum(1 for item in results if item.status == "FAIL")
    timestamp_utc = _now_timestamp()
    _write_report(root, report_file, results, timestamp_utc)

    for item in results:
        print(f"PORTAL_VERIFY|{item.key}|{item.status}|{item.details}")

    print(f"PORTAL_VERIFY|report|PASS|wrote {_rel(root, report_file)}")
    print("PORTAL_VERIFY|report_latest|PASS|updated dist/portal-submission/portal-submission-verify-latest.txt")
    print("PORTAL_VERIFY|report_latest_json|PASS|updated dist/portal-submission/portal-submission-verify-latest.json")

    if fail_count == 0:
        print("PORTAL_VERIFY|summary|PASS|portal submission packet is ready")
        return 0

    print("PORTAL_VERIFY|summary|FAIL|portal submission packet is not ready")
    return 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--packet-json",
        default="dist/portal-submission/portal-submission-packet-latest.json",
        help="Path to packet manifest json (default: dist/portal-submission/portal-submission-packet-latest.json)",
    )
    parser.add_argument(
        "--report-file",
        default="",
        help="Optional explicit report path. Defaults to dist/portal-submission/portal-submission-verify-<timestamp>.txt",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    root = Path(__file__).resolve().parent.parent

    packet_json = Path(args.packet_json)
    if not packet_json.is_absolute():
        packet_json = root / packet_json

    if args.report_file:
        report_file = Path(args.report_file)
        if not report_file.is_absolute():
            report_file = root / report_file
    else:
        report_file = root / "dist" / "portal-submission" / f"portal-submission-verify-{_now_timestamp()}.txt"

    return run(root=root, packet_json=packet_json, report_file=report_file)


if __name__ == "__main__":
    raise SystemExit(main())
