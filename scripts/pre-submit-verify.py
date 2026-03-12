#!/usr/bin/env python3
"""Final pre-submit verifier for submission-form draft references."""

from __future__ import annotations

import argparse
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


def _check_file(root: Path, rel_path: str) -> CheckResult:
    path = root / rel_path
    if path.is_file():
        return CheckResult(rel_path.replace("/", "_"), "PASS", f"found {rel_path}")
    return CheckResult(rel_path.replace("/", "_"), "FAIL", f"missing {rel_path}")


def _check_glob_latest(root: Path, pattern: str, key: str) -> CheckResult:
    matches = sorted(root.glob(pattern))
    if not matches:
        return CheckResult(key, "FAIL", f"missing {pattern}")
    latest = matches[-1]
    return CheckResult(key, "PASS", f"found {_rel(root, latest)}")


def _write_report(
    *,
    root: Path,
    report_file: Path,
    demo_id: str,
    results: list[CheckResult],
    timestamp_utc: str,
) -> None:
    pass_count = sum(1 for item in results if item.status == "PASS")
    fail_count = sum(1 for item in results if item.status == "FAIL")
    overall = "PASS" if fail_count == 0 else "FAIL"

    lines: list[str] = []
    lines.append("HederaShield Final Pre-Submit Verify")
    lines.append(f"Timestamp UTC: {timestamp_utc}")
    lines.append(f"Demo ID: {demo_id}")
    lines.append("")
    lines.append("Summary")
    lines.append(f"- Overall: {overall}")
    lines.append(f"- PASS: {pass_count}")
    lines.append(f"- FAIL: {fail_count}")
    lines.append("")
    lines.append("Checks")
    for item in results:
        lines.append(f"VERIFY|{item.key}|{item.status}|{item.details}")

    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    latest = root / "dist" / "pre-submit-verify-latest.txt"
    latest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(report_file, latest)


def run(root: Path, demo_id: str, report_file: Path) -> int:
    demo_prefix = f"artifacts/demo/{demo_id}"

    required_files = [
        "README.md",
        "SUBMISSION.md",
        "RELEASE_READINESS.md",
        "docs/SUBMISSION_FORM_DRAFT_PACK.md",
        "docs/DEMO_RECORDING_RUNBOOK.md",
        "docs/DEMO_NARRATION_3MIN.md",
        "docs/FINAL_SUBMISSION_CHECKLIST.md",
        "docs/TESTNET_SETUP.md",
        "docs/TESTNET_EVIDENCE.md",
        "docs/DEPLOY_PROOF.md",
        "scripts/pre_submit_guard.sh",
        "dist/submission-bundle.zip",
        "dist/submission-readiness-latest.txt",
        f"{demo_prefix}/harness/report.md",
        f"{demo_prefix}/harness/report.json",
        f"{demo_prefix}/harness/harness.log",
        f"{demo_prefix}/harness/smoke.log",
        f"{demo_prefix}/harness/validator.log",
        f"{demo_prefix}/submission-bundle.zip.sha256",
    ]

    results = [_check_file(root, path) for path in required_files]
    results.append(_check_glob_latest(root, "dist/release-evidence-*.tar.gz", "release_evidence_bundle"))

    for item in results:
        print(f"VERIFY|{item.key}|{item.status}|{item.details}")

    timestamp_utc = _now_timestamp()
    _write_report(
        root=root,
        report_file=report_file,
        demo_id=demo_id,
        results=results,
        timestamp_utc=timestamp_utc,
    )
    print(f"VERIFY|report|PASS|wrote {_rel(root, report_file)}")
    print("VERIFY|report_latest|PASS|updated dist/pre-submit-verify-latest.txt")

    fail_count = sum(1 for item in results if item.status == "FAIL")
    if fail_count == 0:
        print("VERIFY|summary|PASS|pre-submit verification checks passed")
        return 0

    print("VERIFY|summary|FAIL|pre-submit verification checks failed")
    return 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo-id", default="3min-offline", help="Demo ID under artifacts/demo/ (default: 3min-offline)")
    parser.add_argument(
        "--report-file",
        default="",
        help="Optional explicit report path. Defaults to dist/pre-submit-verify-<timestamp>.txt",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    root = Path(__file__).resolve().parent.parent
    timestamp_utc = _now_timestamp()

    if args.report_file:
        report_file = Path(args.report_file)
        if not report_file.is_absolute():
            report_file = root / report_file
    else:
        report_file = root / "dist" / f"pre-submit-verify-{timestamp_utc}.txt"

    return run(root=root, demo_id=args.demo_id, report_file=report_file)


if __name__ == "__main__":
    raise SystemExit(main())
