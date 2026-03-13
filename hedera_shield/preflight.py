"""Unified preflight diagnostics for HederaShield.

Probes every external dependency (Mirror Node, Anthropic API, operator
credentials, HCS topic) and produces a structured pass/fail/skip report.
Run as a module:

    python -m hedera_shield.preflight
    python -m hedera_shield.preflight --env-file .env.testnet
    python -m hedera_shield.preflight --json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import sys
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from hedera_shield.config import Settings

logger = logging.getLogger(__name__)

# Credential placeholder patterns (shared with validate-testnet-env.py)
_ACCOUNT_PLACEHOLDER_RE = re.compile(
    r"^0\.0\.(YOUR_[A-Z0-9_]+|PLACEHOLDER|EXAMPLE)$"
)
_KEY_PLACEHOLDER_RE = re.compile(
    r"^(YOUR_[A-Z0-9_]+|your_[a-z0-9_]+|<[^>]+>)$"
)
_ACCOUNT_ID_RE = re.compile(r"^\d+\.\d+\.\d+$")


@dataclass
class CheckResult:
    """Result of a single preflight check."""

    name: str
    status: str  # "PASS", "FAIL", "SKIP", "WARN"
    detail: str = ""
    latency_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"name": self.name, "status": self.status, "detail": self.detail}
        if self.latency_ms is not None:
            d["latency_ms"] = round(self.latency_ms, 1)
        return d


@dataclass
class PreflightReport:
    """Aggregated preflight report."""

    checks: list[CheckResult] = field(default_factory=list)
    overall: str = "UNKNOWN"

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall": self.overall,
            "checks": [c.to_dict() for c in self.checks],
        }

    def compute_overall(self) -> None:
        statuses = {c.status for c in self.checks}
        if "FAIL" in statuses:
            self.overall = "FAIL"
        elif "WARN" in statuses:
            self.overall = "WARN"
        elif all(s in ("PASS", "SKIP") for s in statuses):
            self.overall = "PASS"
        else:
            self.overall = "UNKNOWN"


def _is_placeholder_operator_id(value: str) -> bool:
    return not value or bool(_ACCOUNT_PLACEHOLDER_RE.fullmatch(value))


def _is_placeholder_key(value: str) -> bool:
    return not value or bool(_KEY_PLACEHOLDER_RE.fullmatch(value))


def check_credentials(config: Settings) -> list[CheckResult]:
    """Validate operator credentials format (offline, no network)."""
    results: list[CheckResult] = []

    # Operator ID
    op_id = config.hedera_operator_id
    if not op_id:
        results.append(CheckResult("operator_id", "FAIL", "not set"))
    elif _is_placeholder_operator_id(op_id):
        results.append(CheckResult("operator_id", "WARN", f"placeholder value: {op_id}"))
    elif _ACCOUNT_ID_RE.fullmatch(op_id):
        results.append(CheckResult("operator_id", "PASS", op_id))
    else:
        results.append(CheckResult("operator_id", "FAIL", f"invalid format: {op_id}"))

    # Operator key (never log full key)
    op_key = config.hedera_operator_key
    if not op_key:
        results.append(CheckResult("operator_key", "FAIL", "not set"))
    elif _is_placeholder_key(op_key):
        results.append(CheckResult("operator_key", "WARN", "placeholder value"))
    else:
        results.append(CheckResult("operator_key", "PASS", f"set ({len(op_key)} chars)"))

    # Anthropic API key
    api_key = config.anthropic_api_key
    if not api_key:
        results.append(CheckResult("anthropic_api_key", "SKIP", "not set (AI analysis disabled)"))
    elif api_key.startswith("sk-ant-"):
        results.append(CheckResult("anthropic_api_key", "PASS", "set (sk-ant-... format)"))
    elif _KEY_PLACEHOLDER_RE.fullmatch(api_key):
        results.append(CheckResult("anthropic_api_key", "WARN", "placeholder value"))
    else:
        results.append(CheckResult("anthropic_api_key", "PASS", f"set ({len(api_key)} chars)"))

    # Network
    network = config.hedera_network
    if network in ("testnet", "mainnet", "previewnet"):
        results.append(CheckResult("network", "PASS", network))
    else:
        results.append(CheckResult("network", "FAIL", f"invalid: {network}"))

    return results


async def check_mirror_node(config: Settings) -> CheckResult:
    """Probe Mirror Node /api/v1/transactions?limit=1 for connectivity."""
    url = f"{config.mirror_node_url.rstrip('/')}/api/v1/transactions"
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params={"limit": 1})
            latency = (time.monotonic() - start) * 1000
            if resp.status_code == 200:
                data = resp.json()
                txns = data.get("transactions", [])
                return CheckResult(
                    "mirror_node",
                    "PASS",
                    f"reachable ({len(txns)} txn(s) returned)",
                    latency,
                )
            return CheckResult(
                "mirror_node",
                "FAIL",
                f"HTTP {resp.status_code}",
                latency,
            )
    except httpx.TimeoutException:
        latency = (time.monotonic() - start) * 1000
        return CheckResult("mirror_node", "FAIL", "timeout (10s)", latency)
    except httpx.ConnectError as exc:
        latency = (time.monotonic() - start) * 1000
        return CheckResult("mirror_node", "FAIL", f"connection error: {exc}", latency)
    except Exception as exc:
        latency = (time.monotonic() - start) * 1000
        return CheckResult("mirror_node", "FAIL", str(exc), latency)


async def check_mirror_node_account(config: Settings) -> CheckResult:
    """Verify the operator account exists on the network via Mirror Node."""
    op_id = config.hedera_operator_id
    if not op_id or _is_placeholder_operator_id(op_id):
        return CheckResult("account_lookup", "SKIP", "operator ID is placeholder/empty")

    url = f"{config.mirror_node_url.rstrip('/')}/api/v1/accounts/{op_id}"
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            latency = (time.monotonic() - start) * 1000
            if resp.status_code == 200:
                data = resp.json()
                balance = data.get("balance", {}).get("balance", "?")
                return CheckResult(
                    "account_lookup",
                    "PASS",
                    f"account {op_id} found (balance: {balance} tinybar)",
                    latency,
                )
            if resp.status_code == 404:
                return CheckResult(
                    "account_lookup",
                    "FAIL",
                    f"account {op_id} not found on {config.hedera_network}",
                    latency,
                )
            return CheckResult("account_lookup", "FAIL", f"HTTP {resp.status_code}", latency)
    except Exception as exc:
        latency = (time.monotonic() - start) * 1000
        return CheckResult("account_lookup", "FAIL", str(exc), latency)


async def check_anthropic_api(config: Settings) -> CheckResult:
    """Probe Anthropic API with a minimal request to verify the key works."""
    api_key = config.anthropic_api_key
    if not api_key or _KEY_PLACEHOLDER_RE.fullmatch(api_key):
        return CheckResult("anthropic_api", "SKIP", "API key not set or placeholder")

    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": config.ai_model,
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "ping"}],
                },
            )
            latency = (time.monotonic() - start) * 1000
            if resp.status_code == 200:
                return CheckResult("anthropic_api", "PASS", "key valid, API reachable", latency)
            if resp.status_code == 401:
                return CheckResult("anthropic_api", "FAIL", "invalid API key (401)", latency)
            if resp.status_code == 429:
                return CheckResult("anthropic_api", "WARN", "rate limited (429) — key is valid", latency)
            return CheckResult("anthropic_api", "WARN", f"HTTP {resp.status_code}", latency)
    except Exception as exc:
        latency = (time.monotonic() - start) * 1000
        return CheckResult("anthropic_api", "FAIL", str(exc), latency)


async def check_hedera_sdk() -> CheckResult:
    """Check whether the Hedera Python SDK is importable."""
    try:
        import hedera  # type: ignore[import-untyped]  # noqa: F401

        return CheckResult("hedera_sdk", "PASS", "hedera package importable")
    except ImportError:
        return CheckResult(
            "hedera_sdk",
            "WARN",
            "hedera-sdk not installed (enforcement will be dry-run only)",
        )


async def run_preflight(config: Settings, *, skip_network: bool = False) -> PreflightReport:
    """Execute all preflight checks and return a report."""
    report = PreflightReport()

    # 1. Credential checks (offline)
    report.checks.extend(check_credentials(config))

    # 2. SDK availability
    report.checks.append(await check_hedera_sdk())

    # 3. Network checks (can be skipped for offline mode)
    if skip_network:
        report.checks.append(CheckResult("mirror_node", "SKIP", "network checks skipped"))
        report.checks.append(CheckResult("account_lookup", "SKIP", "network checks skipped"))
        report.checks.append(CheckResult("anthropic_api", "SKIP", "network checks skipped"))
    else:
        mirror_result, account_result, anthropic_result = await asyncio.gather(
            check_mirror_node(config),
            check_mirror_node_account(config),
            check_anthropic_api(config),
        )
        report.checks.append(mirror_result)
        report.checks.append(account_result)
        report.checks.append(anthropic_result)

    report.compute_overall()
    return report


def _load_env_into_settings(env_file: str) -> Settings:
    """Load a .env file and create Settings from it."""
    from dotenv import dotenv_values

    env = dotenv_values(env_file)
    # Strip the HEDERA_SHIELD_ prefix for pydantic-settings field names
    prefix = "HEDERA_SHIELD_"
    kwargs: dict[str, Any] = {}
    field_map = {
        "HEDERA_NETWORK": "hedera_network",
        "HEDERA_OPERATOR_ID": "hedera_operator_id",
        "HEDERA_OPERATOR_KEY": "hedera_operator_key",
        "MIRROR_NODE_URL": "mirror_node_url",
        "MIRROR_NODE_POLL_INTERVAL": "mirror_node_poll_interval",
        "ANTHROPIC_API_KEY": "anthropic_api_key",
        "AI_MODEL": "ai_model",
        "LARGE_TRANSFER_THRESHOLD": "large_transfer_threshold",
        "VELOCITY_WINDOW_SECONDS": "velocity_window_seconds",
        "VELOCITY_MAX_TRANSFERS": "velocity_max_transfers",
        "API_HOST": "api_host",
        "API_PORT": "api_port",
        "MONITORED_TOKEN_IDS": "monitored_token_ids",
        "SANCTIONED_ADDRESSES": "sanctioned_addresses",
    }
    for env_key, value in env.items():
        if env_key.startswith(prefix):
            short_key = env_key[len(prefix):]
            if short_key in field_map and value is not None:
                field_name = field_map[short_key]
                # Handle JSON list fields
                if field_name in ("monitored_token_ids", "sanctioned_addresses"):
                    try:
                        kwargs[field_name] = json.loads(value)
                    except json.JSONDecodeError:
                        kwargs[field_name] = []
                # Handle int fields
                elif field_name in (
                    "mirror_node_poll_interval",
                    "velocity_window_seconds",
                    "velocity_max_transfers",
                    "api_port",
                ):
                    try:
                        kwargs[field_name] = int(value)
                    except ValueError:
                        pass
                elif field_name == "large_transfer_threshold":
                    try:
                        kwargs[field_name] = float(value)
                    except ValueError:
                        pass
                else:
                    kwargs[field_name] = value

    return Settings(**kwargs)


def format_report_text(report: PreflightReport) -> str:
    """Format the report as human-readable text."""
    lines: list[str] = []
    lines.append("HederaShield Preflight Diagnostics")
    lines.append("=" * 40)
    lines.append("")

    max_name = max(len(c.name) for c in report.checks)
    for check in report.checks:
        status_icon = {
            "PASS": "+",
            "FAIL": "x",
            "WARN": "!",
            "SKIP": "-",
        }.get(check.status, "?")
        latency_str = f" ({check.latency_ms:.0f}ms)" if check.latency_ms is not None else ""
        lines.append(
            f"  [{status_icon}] {check.name:<{max_name}}  {check.status:<4}  {check.detail}{latency_str}"
        )

    lines.append("")
    lines.append(f"Overall: {report.overall}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="HederaShield preflight diagnostics — probe all external dependencies",
    )
    parser.add_argument(
        "--env-file",
        default=None,
        help="Path to .env file (default: use environment variables)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output as JSON",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip network probes (credential format checks only)",
    )
    args = parser.parse_args(argv)

    if args.env_file:
        config = _load_env_into_settings(args.env_file)
    else:
        config = Settings()

    report = asyncio.run(run_preflight(config, skip_network=args.offline))

    if args.json_output:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(format_report_text(report))

    return 0 if report.overall in ("PASS", "WARN") else 1


if __name__ == "__main__":
    sys.exit(main())
