#!/usr/bin/env python3
"""Run an offline end-to-end HederaShield simulation and emit judge-visible artifacts.

Flow:
sample HTS events -> compliance rules engine -> HCS reporting (dry-run) -> report artifacts
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hedera_shield.compliance import ComplianceEngine
from hedera_shield.hcs_reporter import HCSReporter
from hedera_shield.models import TokenTransfer


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sample-events",
        default="demo/sample_hts_events.json",
        help="Path to sample HTS events JSON (default: demo/sample_hts_events.json)",
    )
    parser.add_argument(
        "--output-base-dir",
        default="artifacts/demo/e2e-simulation",
        help="Base output directory for timestamped artifacts",
    )
    parser.add_argument(
        "--timestamp",
        default="",
        help="Optional UTC timestamp folder name (e.g. 20260311T120000Z)",
    )
    parser.add_argument(
        "--topic-id",
        default="0.0.123456",
        help="Demo HCS topic id to record in dry-run results",
    )
    return parser.parse_args()


def _load_sample_events(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        events = payload.get("events", [])
    else:
        events = payload

    if not isinstance(events, list):
        raise ValueError("sample events JSON must contain a list or {'events': [...]} shape")

    normalized: list[dict[str, Any]] = []
    for index, event in enumerate(events, start=1):
        if not isinstance(event, dict):
            raise ValueError(f"event #{index} is not an object")
        normalized.append(event)
    return normalized


def _build_transfers(events: list[dict[str, Any]]) -> list[TokenTransfer]:
    now = datetime.now(timezone.utc)
    base = now - timedelta(seconds=15)
    transfers: list[TokenTransfer] = []

    for idx, event in enumerate(events, start=1):
        tx_id = str(event.get("transaction_id") or f"sim-tx-{idx:03d}")
        token_id = str(event.get("token_id") or "0.0.5555")
        sender = str(event.get("sender") or "0.0.1111")
        receiver = str(event.get("receiver") or "0.0.2222")
        amount = float(event.get("amount") or 0.0)
        offset = int(event.get("seconds_from_start", idx - 1))
        memo = str(event.get("memo") or "")

        transfers.append(
            TokenTransfer(
                transaction_id=tx_id,
                token_id=token_id,
                sender=sender,
                receiver=receiver,
                amount=amount,
                timestamp=base + timedelta(seconds=offset),
                memo=memo,
            )
        )

    return transfers


def _write_artifacts(
    output_dir: Path,
    sample_path: Path,
    transfers: list[TokenTransfer],
    alerts: list[dict[str, Any]],
    hcs_results: list[dict[str, Any]],
    topic_id: str,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    alerts_by_type = Counter(item["alert_type"] for item in alerts)
    alerts_by_severity = Counter(item["severity"] for item in alerts)

    report = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sample_events_path": str(sample_path),
            "hcs_topic_id": topic_id,
            "mode": "offline_dry_run",
        },
        "summary": {
            "sample_events": len(transfers),
            "alerts_generated": len(alerts),
            "hcs_messages_published": len(hcs_results),
            "hcs_statuses": dict(Counter(item.get("status", "unknown") for item in hcs_results)),
            "alerts_by_type": dict(alerts_by_type),
            "alerts_by_severity": dict(alerts_by_severity),
        },
        "transfers": [
            {
                "transaction_id": tx.transaction_id,
                "token_id": tx.token_id,
                "sender": tx.sender,
                "receiver": tx.receiver,
                "amount": tx.amount,
                "timestamp": tx.timestamp.isoformat(),
                "memo": tx.memo,
            }
            for tx in transfers
        ],
        "alerts": alerts,
        "hcs_publish_results": hcs_results,
    }

    json_path = output_dir / "report.json"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# HederaShield E2E Simulation Report",
        "",
        f"- Generated at: `{report['meta']['generated_at']}`",
        f"- Sample events: `{sample_path}`",
        f"- HCS topic: `{topic_id}` (dry-run)",
        "",
        "## Summary",
        "",
        f"- Sample HTS events processed: **{report['summary']['sample_events']}**",
        f"- Compliance alerts generated: **{report['summary']['alerts_generated']}**",
        f"- HCS publish attempts: **{report['summary']['hcs_messages_published']}**",
        f"- HCS statuses: `{json.dumps(report['summary']['hcs_statuses'], sort_keys=True)}`",
        "",
        "## Alert Breakdown",
        "",
        f"- By type: `{json.dumps(report['summary']['alerts_by_type'], sort_keys=True)}`",
        f"- By severity: `{json.dumps(report['summary']['alerts_by_severity'], sort_keys=True)}`",
        "",
        "## Top Alerts",
        "",
    ]

    if alerts:
        for alert in alerts[:5]:
            lines.append(
                "- "
                f"`{alert['alert_id']}` "
                f"[{alert['severity']}] `{alert['alert_type']}` "
                f"tx=`{alert['transaction_id']}` risk=`{alert['risk_score']:.3f}` "
                f"action=`{alert['recommended_action']}`"
            )
    else:
        lines.append("- No alerts generated.")

    lines.extend(
        [
            "",
            "## Output Files",
            "",
            f"- `{json_path}`",
            f"- `{output_dir / 'report.md'}`",
        ]
    )

    md_path = output_dir / "report.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return json_path, md_path


async def _run(args: argparse.Namespace) -> int:
    sample_path = Path(args.sample_events).resolve()
    if not sample_path.is_file():
        print(f"SIM|input|FAIL|sample events file not found: {sample_path}")
        return 1

    timestamp = args.timestamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = Path(args.output_base_dir).resolve() / timestamp

    events = _load_sample_events(sample_path)
    transfers = _build_transfers(events)

    engine = ComplianceEngine(rules_config_path="auto")
    alerts_raw = engine.analyze_batch(transfers)

    reporter = HCSReporter(topic_id=args.topic_id, dry_run=True)
    hcs_results = await reporter.publish_batch(alerts_raw)

    alerts = [
        {
            "alert_id": alert.id,
            "alert_type": alert.alert_type.value,
            "severity": alert.severity.value,
            "risk_score": alert.risk_score,
            "description": alert.description,
            "recommended_action": alert.recommended_action.value,
            "transaction_id": alert.transaction.transaction_id,
            "token_id": alert.transaction.token_id,
            "sender": alert.transaction.sender,
            "receiver": alert.transaction.receiver,
            "amount": alert.transaction.amount,
        }
        for alert in alerts_raw
    ]

    json_path, md_path = _write_artifacts(
        output_dir=output_dir,
        sample_path=sample_path,
        transfers=transfers,
        alerts=alerts,
        hcs_results=hcs_results,
        topic_id=args.topic_id,
    )

    print(f"SIM|input|PASS|loaded {len(transfers)} sample HTS events from {sample_path}")
    print(f"SIM|rules|PASS|generated {len(alerts)} compliance alerts")
    print(f"SIM|hcs|PASS|published {len(hcs_results)} dry-run HCS messages")
    print(f"SIM|artifact|PASS|wrote {json_path} and {md_path}")
    return 0


def main() -> int:
    args = _parse_args()
    import asyncio

    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
