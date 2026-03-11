from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "run-e2e-simulation.py"
SAMPLE_EVENTS = ROOT / "demo" / "sample_hts_events.json"


def test_e2e_simulation_generates_artifacts_and_hcs_dry_run_results(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    script_path = project / "scripts" / "run-e2e-simulation.py"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SCRIPT, script_path)

    hedera_pkg_src = ROOT / "hedera_shield"
    hedera_pkg_dst = project / "hedera_shield"
    shutil.copytree(hedera_pkg_src, hedera_pkg_dst)

    config_src = ROOT / "config"
    config_dst = project / "config"
    shutil.copytree(config_src, config_dst)

    sample_events_path = project / "demo" / "sample_hts_events.json"
    sample_events_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SAMPLE_EVENTS, sample_events_path)

    timestamp = "20260311T120000Z"
    result = subprocess.run(
        [
            "python3",
            str(script_path),
            "--sample-events",
            str(sample_events_path),
            "--output-base-dir",
            "artifacts/demo/e2e-simulation",
            "--timestamp",
            timestamp,
            "--topic-id",
            "0.0.424242",
        ],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "SIM|rules|PASS|" in result.stdout
    assert "SIM|hcs|PASS|" in result.stdout

    out_dir = project / "artifacts" / "demo" / "e2e-simulation" / timestamp
    report_json = out_dir / "report.json"
    report_md = out_dir / "report.md"

    assert report_json.exists()
    assert report_md.exists()

    payload = json.loads(report_json.read_text(encoding="utf-8"))
    assert payload["summary"]["sample_events"] == 8
    assert payload["summary"]["alerts_generated"] > 0
    assert payload["summary"]["hcs_messages_published"] == payload["summary"]["alerts_generated"]
    assert payload["summary"]["hcs_statuses"]["dry_run"] == payload["summary"]["alerts_generated"]
    assert "large_transfer" in payload["summary"]["alerts_by_type"]

    md_content = report_md.read_text(encoding="utf-8")
    assert "HederaShield E2E Simulation Report" in md_content
    assert "HCS topic" in md_content
