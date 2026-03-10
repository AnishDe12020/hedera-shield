#!/usr/bin/env python3
"""Generate compact submit-now packet for portal submission."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REQUIRED_SOURCES = [
    ("portal_packet_md", "dist/portal-submission/portal-submission-packet-latest.md"),
    ("portal_packet_json", "dist/portal-submission/portal-submission-packet-latest.json"),
    ("handoff_playbook_md", "dist/handoff-playbook/human-handoff-playbook-latest.md"),
    ("submission_freeze_md", "dist/submission-freeze/submission-freeze-latest.md"),
    ("push_status_txt", "dist/portal-submission/push-status-latest.txt"),
]


def _abs(path: Path) -> str:
    return str(path.resolve())


def _write_missing_report(report_path: Path, missing: list[tuple[str, Path]]) -> None:
    lines = ["# Submit-Now Missing Files Report", ""]
    if missing:
        lines.append(f"MISSING_COUNT: {len(missing)}")
        lines.append("")
        for key, path in missing:
            lines.append(f"- {key}: {_abs(path)}")
    else:
        lines.append("MISSING_COUNT: 0")
        lines.append("")
        lines.append("- none")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_checklist(path: Path) -> None:
    lines = [
        "# Submit-Now Checklist",
        "",
        "1. Open `portal-submission-packet-latest.md` and confirm summary text is final.",
        "2. Open `portal-submission-packet-latest.json` and ensure metadata paths resolve.",
        "3. Open `human-handoff-playbook-latest.md` for operator escalation notes.",
        "4. Open `submission-freeze-latest.md` and confirm commit/artifact freeze snapshot.",
        "5. Open `push-status-latest.txt` and confirm latest push result before submit.",
        "6. Upload packet content in the portal form fields as required.",
        "7. Attach/enter the freeze manifest details in portal evidence fields.",
        "8. Submit and save confirmation ID/screenshot in sprint notes.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_index(path: Path, packet_files: list[Path], source_pairs: list[tuple[str, Path]], checklist_file: Path) -> None:
    action_steps = [
        "Verify portal packet markdown content.",
        "Verify portal packet json content.",
        "Verify handoff playbook for escalation path.",
        "Verify freeze manifest consistency.",
        "Check latest push-status before submit.",
        "Paste/upload required items in portal.",
        "Submit the portal form.",
        "Record confirmation artifact.",
    ]

    lines = [
        "# Submit-Now Index",
        "",
        "## Packet Files (Absolute Paths)",
    ]
    for file_path in sorted(packet_files, key=lambda p: p.name):
        lines.append(f"- {_abs(file_path)}")

    lines.extend([
        "",
        "## Source Files (Absolute Paths)",
    ])
    for key, source in source_pairs:
        lines.append(f"- {key}: {_abs(source)}")

    lines.extend([
        "",
        "## Ordered Action List (<=10)",
    ])
    for idx, step in enumerate(action_steps, start=1):
        lines.append(f"{idx}. {step}")

    lines.extend([
        "",
        "## Checklist",
        f"- {_abs(checklist_file)}",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(root: Path, output_dir: Path) -> int:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    missing_report = output_dir / "missing-files-report.txt"

    source_pairs = [(key, root / rel) for key, rel in REQUIRED_SOURCES]
    missing = [(key, path) for key, path in source_pairs if not path.exists()]
    _write_missing_report(missing_report, missing)
    if missing:
        print(f"SUBMIT_NOW|missing_report|PASS|wrote {missing_report.relative_to(root)}")
        print("SUBMIT_NOW|summary|FAIL|required files missing; see missing-files-report.txt", file=sys.stderr)
        return 1

    copied_files: list[Path] = []
    for _, source in source_pairs:
        target = output_dir / source.name
        shutil.copyfile(source, target)
        copied_files.append(target)

    checklist_file = output_dir / "SUBMIT_NOW_CHECKLIST.md"
    _write_checklist(checklist_file)

    index_file = output_dir / "SUBMIT_NOW_INDEX.md"
    packet_files = copied_files + [missing_report, checklist_file]
    _write_index(index_file, packet_files, source_pairs, checklist_file)

    referenced = [path for _, path in source_pairs] + packet_files + [index_file]
    missing_after_build = [path for path in referenced if not path.exists()]
    if missing_after_build:
        for path in missing_after_build:
            print(f"SUBMIT_NOW|validate|FAIL|missing {_abs(path)}", file=sys.stderr)
        print("SUBMIT_NOW|summary|FAIL|post-build reference validation failed", file=sys.stderr)
        return 1

    print(f"SUBMIT_NOW|missing_report|PASS|wrote {missing_report.relative_to(root)}")
    for path in copied_files:
        print(f"SUBMIT_NOW|copy|PASS|{path.relative_to(root)}")
    print(f"SUBMIT_NOW|checklist|PASS|wrote {checklist_file.relative_to(root)}")
    print(f"SUBMIT_NOW|index|PASS|wrote {index_file.relative_to(root)}")
    print(f"SUBMIT_NOW|summary|PASS|packet ready at {output_dir.relative_to(root)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="dist/submit-now",
        help="Output directory for submit-now packet (default: dist/submit-now)",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = root / output_dir

    return run(root=root, output_dir=output_dir)


if __name__ == "__main__":
    raise SystemExit(main())
