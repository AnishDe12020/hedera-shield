#!/usr/bin/env python3
"""Generate submission-ready evidence artifacts for integration harness runs."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


def _status(exit_code: int | None) -> str:
    if exit_code is None:
        return "SKIP"
    return "PASS" if exit_code == 0 else "FAIL"


def _read_snippet(path: Path, max_lines: int) -> str:
    if not path.exists():
        return "(missing artifact)"

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines:
        return "(no output)"
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join(lines[:max_lines] + [f"... ({len(lines) - max_lines} lines omitted)"])


def _append_log_section(parts: list[str], title: str, path: Path, max_lines: int) -> None:
    parts.append(f"## {title}")
    parts.append(f"- File: `{path}`")
    parts.append("```text")
    parts.append(_read_snippet(path, max_lines))
    parts.append("```")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate integration harness evidence report")
    parser.add_argument("--mode", required=True, choices=("mock", "real"))
    parser.add_argument("--effective-mode", required=True, choices=("mock", "real"))
    parser.add_argument("--dry-run-fallback", required=True, choices=("0", "1"))
    parser.add_argument("--dry-run-reason", default="")
    parser.add_argument("--env-file", required=True)
    parser.add_argument("--artifacts-dir", required=True)
    parser.add_argument("--validator-exit", required=True, type=int)
    parser.add_argument("--smoke-exit", required=True, type=int)
    parser.add_argument(
        "--integration-exit",
        type=int,
        default=None,
        help="Exit code for live integration pytest; omit if skipped",
    )
    parser.add_argument("--harness-exit", required=True, type=int)
    parser.add_argument("--max-snippet-lines", type=int, default=40)
    args = parser.parse_args()

    artifacts_dir = Path(args.artifacts_dir).resolve()
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    validator_log = artifacts_dir / "validator.log"
    smoke_log = artifacts_dir / "smoke.log"
    integration_log = artifacts_dir / "integration.log"
    harness_log = artifacts_dir / "harness.log"

    summary = {
        "timestamp_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "mode": args.mode,
        "effective_mode": args.effective_mode,
        "dry_run_fallback": args.dry_run_fallback == "1",
        "dry_run_reason": args.dry_run_reason,
        "env_file": str(Path(args.env_file).resolve()),
        "artifacts_dir": str(artifacts_dir),
        "checks": {
            "validator": {"exit_code": args.validator_exit, "status": _status(args.validator_exit)},
            "smoke": {"exit_code": args.smoke_exit, "status": _status(args.smoke_exit)},
            "integration_pytest": {
                "exit_code": args.integration_exit,
                "status": _status(args.integration_exit),
            },
            "harness": {"exit_code": args.harness_exit, "status": _status(args.harness_exit)},
        },
    }

    (artifacts_dir / "report.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    parts: list[str] = []
    parts.append("# HederaShield Integration Harness Evidence")
    parts.append("")
    parts.append(f"- Generated (UTC): `{summary['timestamp_utc']}`")
    parts.append(f"- Mode: `{args.mode}`")
    parts.append(f"- Effective mode: `{args.effective_mode}`")
    parts.append(f"- Dry-run fallback: `{'yes' if args.dry_run_fallback == '1' else 'no'}`")
    if args.dry_run_reason:
        parts.append(f"- Dry-run reason: `{args.dry_run_reason}`")
    parts.append(f"- Env file: `{summary['env_file']}`")
    parts.append("")
    parts.append("## Check Summary")
    for name, result in summary["checks"].items():
        parts.append(
            f"- `{name}`: `{result['status']}`"
            + (f" (exit `{result['exit_code']}`)" if result["exit_code"] is not None else "")
        )

    parts.append("")
    _append_log_section(parts, "Harness Log", harness_log, args.max_snippet_lines)
    parts.append("")
    _append_log_section(parts, "Validator Log", validator_log, args.max_snippet_lines)
    parts.append("")
    _append_log_section(parts, "Smoke Log", smoke_log, args.max_snippet_lines)
    parts.append("")
    _append_log_section(parts, "Integration Pytest Log", integration_log, args.max_snippet_lines)
    parts.append("")
    parts.append("## Submission Snippet")
    parts.append("Use these files in your submission package:")
    parts.append(f"- `{artifacts_dir / 'report.md'}`")
    parts.append(f"- `{artifacts_dir / 'report.json'}`")
    parts.append(f"- `{validator_log}`")
    parts.append(f"- `{smoke_log}`")
    parts.append(f"- `{integration_log}`")
    parts.append(f"- `{harness_log}`")

    (artifacts_dir / "report.md").write_text("\n".join(parts) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
