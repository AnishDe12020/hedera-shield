"""Tests for the preflight diagnostics module."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from hedera_shield.config import Settings
from hedera_shield.preflight import (
    CheckResult,
    PreflightReport,
    check_credentials,
    check_mirror_node,
    check_mirror_node_account,
    check_anthropic_api,
    check_hedera_sdk,
    format_report_text,
    main,
    run_preflight,
    _is_placeholder_operator_id,
    _is_placeholder_key,
)


# ---------------------------------------------------------------------------
# Helper to build a mock httpx.AsyncClient context manager
# ---------------------------------------------------------------------------


def _mock_async_client(response: httpx.Response | None = None, *, side_effect=None):
    """Return a patch context that replaces httpx.AsyncClient with a mock."""
    mock_client = AsyncMock()
    if side_effect:
        mock_client.get.side_effect = side_effect
        mock_client.post.side_effect = side_effect
    elif response is not None:
        mock_client.get.return_value = response
        mock_client.post.return_value = response

    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock_client)
    cm.__aexit__ = AsyncMock(return_value=False)

    return patch("hedera_shield.preflight.httpx.AsyncClient", return_value=cm)


def _make_response(status_code: int = 200, json_data: dict | None = None) -> httpx.Response:
    """Build a real httpx.Response for use in tests."""
    resp = httpx.Response(status_code, json=json_data or {})
    return resp


# ---------------------------------------------------------------------------
# Placeholder detection
# ---------------------------------------------------------------------------


class TestPlaceholderDetection:
    def test_empty_is_placeholder_id(self):
        assert _is_placeholder_operator_id("")

    def test_your_placeholder_id(self):
        assert _is_placeholder_operator_id("0.0.YOUR_ACCOUNT_ID")

    def test_real_account_is_not_placeholder(self):
        assert not _is_placeholder_operator_id("0.0.12345")

    def test_empty_is_placeholder_key(self):
        assert _is_placeholder_key("")

    def test_your_placeholder_key(self):
        assert _is_placeholder_key("YOUR_ED25519_PRIVATE_KEY")

    def test_hex_key_is_not_placeholder(self):
        assert not _is_placeholder_key("a" * 64)


# ---------------------------------------------------------------------------
# Credential checks (offline)
# ---------------------------------------------------------------------------


class TestCheckCredentials:
    def test_all_valid(self):
        config = Settings(
            hedera_network="testnet",
            hedera_operator_id="0.0.12345",
            hedera_operator_key="a" * 64,
            anthropic_api_key="sk-ant-test123",
        )
        results = check_credentials(config)
        statuses = {r.name: r.status for r in results}
        assert statuses["operator_id"] == "PASS"
        assert statuses["operator_key"] == "PASS"
        assert statuses["anthropic_api_key"] == "PASS"
        assert statuses["network"] == "PASS"

    def test_placeholders_warn(self):
        config = Settings(
            hedera_network="testnet",
            hedera_operator_id="0.0.YOUR_ACCOUNT_ID",
            hedera_operator_key="YOUR_ED25519_PRIVATE_KEY",
            anthropic_api_key="YOUR_API_KEY",
        )
        results = check_credentials(config)
        statuses = {r.name: r.status for r in results}
        assert statuses["operator_id"] == "WARN"
        assert statuses["operator_key"] == "WARN"
        assert statuses["anthropic_api_key"] == "WARN"

    def test_empty_credentials_fail_or_skip(self):
        config = Settings(
            hedera_network="testnet",
            hedera_operator_id="",
            hedera_operator_key="",
            anthropic_api_key="",
        )
        results = check_credentials(config)
        statuses = {r.name: r.status for r in results}
        assert statuses["operator_id"] == "FAIL"
        assert statuses["operator_key"] == "FAIL"
        assert statuses["anthropic_api_key"] == "SKIP"

    def test_invalid_network_fails(self):
        config = Settings(hedera_network="invalid")
        results = check_credentials(config)
        network_check = [r for r in results if r.name == "network"][0]
        assert network_check.status == "FAIL"

    def test_invalid_operator_id_format(self):
        config = Settings(hedera_operator_id="not-an-id")
        results = check_credentials(config)
        id_check = [r for r in results if r.name == "operator_id"][0]
        assert id_check.status == "FAIL"


# ---------------------------------------------------------------------------
# Mirror Node check
# ---------------------------------------------------------------------------


class TestCheckMirrorNode:
    @pytest.mark.asyncio
    async def test_mirror_node_pass(self):
        resp = _make_response(200, {"transactions": [{"transaction_id": "0.0.1-123"}]})
        config = Settings(mirror_node_url="https://testnet.mirrornode.hedera.com")
        with _mock_async_client(resp):
            result = await check_mirror_node(config)
        assert result.status == "PASS"
        assert result.latency_ms is not None

    @pytest.mark.asyncio
    async def test_mirror_node_http_error(self):
        resp = _make_response(500)
        config = Settings(mirror_node_url="https://testnet.mirrornode.hedera.com")
        with _mock_async_client(resp):
            result = await check_mirror_node(config)
        assert result.status == "FAIL"
        assert "500" in result.detail

    @pytest.mark.asyncio
    async def test_mirror_node_timeout(self):
        config = Settings(mirror_node_url="https://192.0.2.1")
        with _mock_async_client(side_effect=httpx.TimeoutException("timed out")):
            result = await check_mirror_node(config)
        assert result.status == "FAIL"
        assert "timeout" in result.detail

    @pytest.mark.asyncio
    async def test_mirror_node_connect_error(self):
        config = Settings(mirror_node_url="https://192.0.2.1")
        with _mock_async_client(side_effect=httpx.ConnectError("refused")):
            result = await check_mirror_node(config)
        assert result.status == "FAIL"
        assert "connection error" in result.detail


# ---------------------------------------------------------------------------
# Account lookup
# ---------------------------------------------------------------------------


class TestCheckMirrorNodeAccount:
    @pytest.mark.asyncio
    async def test_placeholder_skipped(self):
        config = Settings(hedera_operator_id="0.0.YOUR_ACCOUNT_ID")
        result = await check_mirror_node_account(config)
        assert result.status == "SKIP"

    @pytest.mark.asyncio
    async def test_account_found(self):
        resp = _make_response(200, {"account": "0.0.12345", "balance": {"balance": 5000000}})
        config = Settings(
            hedera_operator_id="0.0.12345",
            mirror_node_url="https://testnet.mirrornode.hedera.com",
        )
        with _mock_async_client(resp):
            result = await check_mirror_node_account(config)
        assert result.status == "PASS"
        assert "5000000" in result.detail

    @pytest.mark.asyncio
    async def test_account_not_found(self):
        resp = _make_response(404)
        config = Settings(
            hedera_operator_id="0.0.99999",
            mirror_node_url="https://testnet.mirrornode.hedera.com",
        )
        with _mock_async_client(resp):
            result = await check_mirror_node_account(config)
        assert result.status == "FAIL"
        assert "not found" in result.detail


# ---------------------------------------------------------------------------
# Anthropic API check
# ---------------------------------------------------------------------------


class TestCheckAnthropicApi:
    @pytest.mark.asyncio
    async def test_no_key_skipped(self):
        config = Settings(anthropic_api_key="")
        result = await check_anthropic_api(config)
        assert result.status == "SKIP"

    @pytest.mark.asyncio
    async def test_placeholder_skipped(self):
        config = Settings(anthropic_api_key="YOUR_API_KEY")
        result = await check_anthropic_api(config)
        assert result.status == "SKIP"

    @pytest.mark.asyncio
    async def test_valid_key(self):
        resp = _make_response(200, {"id": "msg_test", "content": [{"text": ""}]})
        config = Settings(anthropic_api_key="sk-ant-real-key")
        with _mock_async_client(resp):
            result = await check_anthropic_api(config)
        assert result.status == "PASS"

    @pytest.mark.asyncio
    async def test_invalid_key(self):
        resp = _make_response(401)
        config = Settings(anthropic_api_key="sk-ant-bad-key")
        with _mock_async_client(resp):
            result = await check_anthropic_api(config)
        assert result.status == "FAIL"
        assert "401" in result.detail

    @pytest.mark.asyncio
    async def test_rate_limited_is_warn(self):
        resp = _make_response(429)
        config = Settings(anthropic_api_key="sk-ant-valid-key")
        with _mock_async_client(resp):
            result = await check_anthropic_api(config)
        assert result.status == "WARN"


# ---------------------------------------------------------------------------
# SDK check
# ---------------------------------------------------------------------------


class TestCheckHederaSdk:
    @pytest.mark.asyncio
    async def test_sdk_not_installed(self):
        result = await check_hedera_sdk()
        # In the test environment, hedera-sdk is likely not installed
        assert result.status in ("PASS", "WARN")


# ---------------------------------------------------------------------------
# Full preflight run
# ---------------------------------------------------------------------------


class TestRunPreflight:
    @pytest.mark.asyncio
    async def test_offline_mode(self):
        config = Settings(
            hedera_network="testnet",
            hedera_operator_id="0.0.12345",
            hedera_operator_key="a" * 64,
        )
        report = await run_preflight(config, skip_network=True)
        assert report.overall in ("PASS", "WARN")
        names = {c.name for c in report.checks}
        assert "operator_id" in names
        assert "mirror_node" in names
        # Network checks should be SKIP in offline mode
        mirror = [c for c in report.checks if c.name == "mirror_node"][0]
        assert mirror.status == "SKIP"

    @pytest.mark.asyncio
    async def test_overall_fail_on_bad_config(self):
        config = Settings(hedera_network="invalid", hedera_operator_id="bad")
        report = await run_preflight(config, skip_network=True)
        assert report.overall == "FAIL"


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------


class TestReportFormatting:
    def test_text_format(self):
        report = PreflightReport(
            checks=[
                CheckResult("test_check", "PASS", "all good", 42.5),
                CheckResult("another", "FAIL", "broken"),
            ]
        )
        report.compute_overall()
        text = format_report_text(report)
        assert "HederaShield Preflight Diagnostics" in text
        assert "PASS" in text
        assert "FAIL" in text
        assert "42ms" in text

    def test_json_format(self):
        report = PreflightReport(
            checks=[CheckResult("x", "PASS", "ok")],
        )
        report.compute_overall()
        d = report.to_dict()
        assert d["overall"] == "PASS"
        assert len(d["checks"]) == 1


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


class TestCli:
    def test_offline_mode_cli(self, tmp_path):
        env_file = tmp_path / ".env.test"
        env_file.write_text(
            "\n".join([
                "HEDERA_SHIELD_HEDERA_NETWORK=testnet",
                "HEDERA_SHIELD_HEDERA_OPERATOR_ID=0.0.12345",
                "HEDERA_SHIELD_HEDERA_OPERATOR_KEY=" + "a" * 64,
                "HEDERA_SHIELD_MIRROR_NODE_URL=https://testnet.mirrornode.hedera.com",
                "HEDERA_SHIELD_MIRROR_NODE_POLL_INTERVAL=10",
                "HEDERA_SHIELD_ANTHROPIC_API_KEY=",
                "HEDERA_SHIELD_AI_MODEL=claude-sonnet-4-20250514",
                "HEDERA_SHIELD_LARGE_TRANSFER_THRESHOLD=10000",
                "HEDERA_SHIELD_VELOCITY_WINDOW_SECONDS=3600",
                "HEDERA_SHIELD_VELOCITY_MAX_TRANSFERS=50",
                "HEDERA_SHIELD_API_HOST=0.0.0.0",
                "HEDERA_SHIELD_API_PORT=8000",
                'HEDERA_SHIELD_MONITORED_TOKEN_IDS=[]',
                'HEDERA_SHIELD_SANCTIONED_ADDRESSES=[]',
            ]),
            encoding="utf-8",
        )
        exit_code = main(["--env-file", str(env_file), "--offline"])
        assert exit_code == 0

    def test_json_output(self, tmp_path, capsys):
        env_file = tmp_path / ".env.test"
        env_file.write_text(
            "\n".join([
                "HEDERA_SHIELD_HEDERA_NETWORK=testnet",
                "HEDERA_SHIELD_HEDERA_OPERATOR_ID=0.0.12345",
                "HEDERA_SHIELD_HEDERA_OPERATOR_KEY=" + "a" * 64,
                "HEDERA_SHIELD_MIRROR_NODE_URL=https://testnet.mirrornode.hedera.com",
                "HEDERA_SHIELD_MIRROR_NODE_POLL_INTERVAL=10",
                "HEDERA_SHIELD_ANTHROPIC_API_KEY=",
                "HEDERA_SHIELD_AI_MODEL=claude-sonnet-4-20250514",
                "HEDERA_SHIELD_LARGE_TRANSFER_THRESHOLD=10000",
                "HEDERA_SHIELD_VELOCITY_WINDOW_SECONDS=3600",
                "HEDERA_SHIELD_VELOCITY_MAX_TRANSFERS=50",
                "HEDERA_SHIELD_API_HOST=0.0.0.0",
                "HEDERA_SHIELD_API_PORT=8000",
                'HEDERA_SHIELD_MONITORED_TOKEN_IDS=[]',
                'HEDERA_SHIELD_SANCTIONED_ADDRESSES=[]',
            ]),
            encoding="utf-8",
        )
        exit_code = main(["--env-file", str(env_file), "--offline", "--json"])
        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "overall" in data
        assert "checks" in data
