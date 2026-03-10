"""Tests for the FastAPI REST API endpoints."""

import csv
import io
import pytest
import pytest_asyncio
import httpx
from datetime import datetime, timezone

from hedera_shield.api import app, compliance_engine, enforcer
from hedera_shield.models import (
    Alert,
    AlertType,
    Severity,
    TokenTransfer,
)


@pytest.fixture(autouse=True)
def reset_state():
    """Reset shared state between tests."""
    compliance_engine.alerts.clear()
    compliance_engine.rules = list(compliance_engine.rules[:5])  # Keep default rules
    enforcer.action_log.clear()
    yield

@pytest_asyncio.fixture
async def client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as test_client:
        yield test_client


def _seed_alert() -> Alert:
    """Create a test alert in the compliance engine."""
    transfer = TokenTransfer(
        transaction_id="tx-test",
        token_id="0.0.5555",
        sender="0.0.1111",
        receiver="0.0.2222",
        amount=50000.0,
        timestamp=datetime.now(timezone.utc),
    )
    alert = Alert(
        id="alert-test-001",
        alert_type=AlertType.LARGE_TRANSFER,
        severity=Severity.HIGH,
        transaction=transfer,
        description="Test alert",
        risk_score=0.8,
    )
    compliance_engine.alerts.append(alert)
    return alert


class TestHealthAndStatus:
    @pytest.mark.asyncio
    async def test_health_check(self, client: httpx.AsyncClient) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_status(self, client: httpx.AsyncClient) -> None:
        resp = await client.get("/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "running"
        assert "total_alerts" in data
        assert "uptime_seconds" in data


class TestAlerts:
    @pytest.mark.asyncio
    async def test_get_alerts_empty(self, client: httpx.AsyncClient) -> None:
        resp = await client.get("/alerts")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_get_alerts_with_data(self, client: httpx.AsyncClient) -> None:
        _seed_alert()
        resp = await client.get("/alerts")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["id"] == "alert-test-001"

    @pytest.mark.asyncio
    async def test_get_unresolved_alerts(self, client: httpx.AsyncClient) -> None:
        alert = _seed_alert()
        alert.resolved = True

        resp = await client.get("/alerts?unresolved_only=true")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_resolve_alert(self, client: httpx.AsyncClient) -> None:
        _seed_alert()
        resp = await client.post("/alerts/alert-test-001/resolve")
        assert resp.status_code == 200
        assert resp.json()["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_resolve_nonexistent_alert(self, client: httpx.AsyncClient) -> None:
        resp = await client.post("/alerts/fake-id/resolve")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_export_audit_csv_empty(self, client: httpx.AsyncClient) -> None:
        resp = await client.get("/compliance/audit.csv")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/csv")
        assert "attachment; filename=\"compliance_audit.csv\"" in resp.headers.get(
            "content-disposition", ""
        )

        rows = list(csv.reader(io.StringIO(resp.text)))
        assert len(rows) == 1  # Header only
        assert rows[0][0] == "alert_id"
        assert rows[0][-1] == "transaction_timestamp"

    @pytest.mark.asyncio
    async def test_export_audit_csv_with_data_and_filter(self, client: httpx.AsyncClient) -> None:
        alert = _seed_alert()
        resp = await client.get("/compliance/audit.csv")
        assert resp.status_code == 200
        rows = list(csv.reader(io.StringIO(resp.text)))
        assert len(rows) == 2
        assert rows[1][0] == alert.id
        assert rows[1][3] == alert.alert_type.value

        alert.resolved = True
        filtered = await client.get("/compliance/audit.csv?unresolved_only=true")
        filtered_rows = list(csv.reader(io.StringIO(filtered.text)))
        assert len(filtered_rows) == 1  # Header only when only alert is resolved


class TestRules:
    @pytest.mark.asyncio
    async def test_get_rules(self, client: httpx.AsyncClient) -> None:
        resp = await client.get("/rules")
        assert resp.status_code == 200
        rules = resp.json()
        assert len(rules) >= 3  # Default rules

    @pytest.mark.asyncio
    async def test_add_rule(self, client: httpx.AsyncClient) -> None:
        rule = {
            "rule": {
                "id": "rule-custom",
                "name": "Custom Rule",
                "description": "A test rule",
                "alert_type": "large_transfer",
                "severity": "low",
            }
        }
        resp = await client.post("/rules", json=rule)
        assert resp.status_code == 200
        assert resp.json()["id"] == "rule-custom"

    @pytest.mark.asyncio
    async def test_delete_rule(self, client: httpx.AsyncClient) -> None:
        resp = await client.delete("/rules/rule-large-transfer")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_nonexistent_rule(self, client: httpx.AsyncClient) -> None:
        resp = await client.delete("/rules/fake-id")
        assert resp.status_code == 404


class TestTransactions:
    @pytest.mark.asyncio
    async def test_get_transactions_no_tokens(self, client: httpx.AsyncClient) -> None:
        resp = await client.get("/transactions")
        assert resp.status_code == 200
        data = resp.json()
        assert "transactions" in data


class TestEnforcement:
    @pytest.mark.asyncio
    async def test_enforce_dry_run(self, client: httpx.AsyncClient) -> None:
        resp = await client.post(
            "/enforce",
            json={
                "action": "freeze",
                "token_id": "0.0.5555",
                "account_id": "0.0.1111",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "dry_run"
        assert data["action"] == "freeze"
