"""Tests for the FastAPI REST API endpoints."""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from hedera_shield.api import app, compliance_engine, enforcer
from hedera_shield.models import (
    Alert,
    AlertType,
    ComplianceRule,
    EnforcementAction,
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


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


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
    def test_health_check(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_status(self, client: TestClient) -> None:
        resp = client.get("/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "running"
        assert "total_alerts" in data
        assert "uptime_seconds" in data


class TestAlerts:
    def test_get_alerts_empty(self, client: TestClient) -> None:
        resp = client.get("/alerts")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_alerts_with_data(self, client: TestClient) -> None:
        _seed_alert()
        resp = client.get("/alerts")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["id"] == "alert-test-001"

    def test_get_unresolved_alerts(self, client: TestClient) -> None:
        alert = _seed_alert()
        alert.resolved = True

        resp = client.get("/alerts?unresolved_only=true")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_resolve_alert(self, client: TestClient) -> None:
        _seed_alert()
        resp = client.post("/alerts/alert-test-001/resolve")
        assert resp.status_code == 200
        assert resp.json()["status"] == "resolved"

    def test_resolve_nonexistent_alert(self, client: TestClient) -> None:
        resp = client.post("/alerts/fake-id/resolve")
        assert resp.status_code == 404


class TestRules:
    def test_get_rules(self, client: TestClient) -> None:
        resp = client.get("/rules")
        assert resp.status_code == 200
        rules = resp.json()
        assert len(rules) >= 3  # Default rules

    def test_add_rule(self, client: TestClient) -> None:
        rule = {
            "rule": {
                "id": "rule-custom",
                "name": "Custom Rule",
                "description": "A test rule",
                "alert_type": "large_transfer",
                "severity": "low",
            }
        }
        resp = client.post("/rules", json=rule)
        assert resp.status_code == 200
        assert resp.json()["id"] == "rule-custom"

    def test_delete_rule(self, client: TestClient) -> None:
        resp = client.delete("/rules/rule-large-transfer")
        assert resp.status_code == 200

    def test_delete_nonexistent_rule(self, client: TestClient) -> None:
        resp = client.delete("/rules/fake-id")
        assert resp.status_code == 404


class TestTransactions:
    def test_get_transactions_no_tokens(self, client: TestClient) -> None:
        resp = client.get("/transactions")
        assert resp.status_code == 200
        data = resp.json()
        assert "transactions" in data


class TestEnforcement:
    def test_enforce_dry_run(self, client: TestClient) -> None:
        resp = client.post(
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
