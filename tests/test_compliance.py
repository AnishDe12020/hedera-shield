"""Tests for the compliance rule engine."""

import pytest
from datetime import datetime, timezone

from hedera_shield.config import Settings
from hedera_shield.compliance import ComplianceEngine
from hedera_shield.models import (
    AlertType,
    ComplianceRule,
    Severity,
    TokenTransfer,
)


@pytest.fixture
def config() -> Settings:
    return Settings(
        large_transfer_threshold=1000.0,
        velocity_window_seconds=3600,
        velocity_max_transfers=3,
        sanctioned_addresses=["0.0.6666", "0.0.7777"],
    )


@pytest.fixture
def engine(config: Settings) -> ComplianceEngine:
    return ComplianceEngine(config=config)


def _make_transfer(
    sender: str = "0.0.1111",
    receiver: str = "0.0.2222",
    amount: float = 100.0,
    token_id: str = "0.0.5555",
) -> TokenTransfer:
    return TokenTransfer(
        transaction_id="tx-test-001",
        token_id=token_id,
        sender=sender,
        receiver=receiver,
        amount=amount,
        timestamp=datetime.now(timezone.utc),
    )


def test_large_transfer_detection(engine: ComplianceEngine) -> None:
    """Transfers above threshold should trigger an alert."""
    transfer = _make_transfer(amount=5000.0)
    alerts = engine.analyze(transfer)

    large_alerts = [a for a in alerts if a.alert_type == AlertType.LARGE_TRANSFER]
    assert len(large_alerts) == 1
    assert large_alerts[0].severity == Severity.HIGH
    assert large_alerts[0].risk_score > 0


def test_small_transfer_no_alert(engine: ComplianceEngine) -> None:
    """Transfers below threshold should not trigger an alert."""
    transfer = _make_transfer(amount=100.0)
    alerts = engine.analyze(transfer)

    large_alerts = [a for a in alerts if a.alert_type == AlertType.LARGE_TRANSFER]
    assert len(large_alerts) == 0


def test_velocity_breach(engine: ComplianceEngine) -> None:
    """Exceeding transfer velocity should trigger an alert."""
    # Send max_transfers from the same account
    alerts = []
    for i in range(4):
        transfer = _make_transfer(sender="0.0.9999", amount=10.0)
        transfer.transaction_id = f"tx-velocity-{i}"
        alerts.extend(engine.analyze(transfer))

    velocity_alerts = [a for a in alerts if a.alert_type == AlertType.VELOCITY_BREACH]
    assert len(velocity_alerts) >= 1


def test_sanctioned_sender(engine: ComplianceEngine) -> None:
    """Transfers from sanctioned addresses should trigger a critical alert."""
    transfer = _make_transfer(sender="0.0.6666")
    alerts = engine.analyze(transfer)

    sanctioned_alerts = [a for a in alerts if a.alert_type == AlertType.SANCTIONED_ADDRESS]
    assert len(sanctioned_alerts) == 1
    assert sanctioned_alerts[0].severity == Severity.CRITICAL
    assert sanctioned_alerts[0].risk_score == 1.0


def test_sanctioned_receiver(engine: ComplianceEngine) -> None:
    """Transfers to sanctioned addresses should trigger a critical alert."""
    transfer = _make_transfer(receiver="0.0.7777")
    alerts = engine.analyze(transfer)

    sanctioned_alerts = [a for a in alerts if a.alert_type == AlertType.SANCTIONED_ADDRESS]
    assert len(sanctioned_alerts) == 1


def test_multiple_rules_fire(engine: ComplianceEngine) -> None:
    """A single transfer can trigger multiple rules."""
    transfer = _make_transfer(sender="0.0.6666", amount=5000.0)
    alerts = engine.analyze(transfer)

    alert_types = {a.alert_type for a in alerts}
    assert AlertType.LARGE_TRANSFER in alert_types
    assert AlertType.SANCTIONED_ADDRESS in alert_types


def test_add_and_remove_rule(engine: ComplianceEngine) -> None:
    """Rules can be added and removed dynamically."""
    custom = ComplianceRule(
        id="rule-custom",
        name="Custom Rule",
        description="Test rule",
        alert_type=AlertType.LARGE_TRANSFER,
        severity=Severity.LOW,
    )
    engine.add_rule(custom)
    assert any(r.id == "rule-custom" for r in engine.get_rules())

    engine.remove_rule("rule-custom")
    assert not any(r.id == "rule-custom" for r in engine.get_rules())


def test_disabled_rule_skipped(engine: ComplianceEngine) -> None:
    """Disabled rules should not generate alerts."""
    for rule in engine.rules:
        rule.enabled = False

    transfer = _make_transfer(sender="0.0.6666", amount=50000.0)
    alerts = engine.analyze(transfer)
    assert len(alerts) == 0


def test_resolve_alert(engine: ComplianceEngine) -> None:
    """Alerts can be resolved."""
    transfer = _make_transfer(amount=5000.0)
    alerts = engine.analyze(transfer)

    for alert in alerts:
        assert engine.resolve_alert(alert.id) is True
    assert engine.get_alerts(unresolved_only=True) == []


def test_resolve_nonexistent_alert(engine: ComplianceEngine) -> None:
    """Resolving a nonexistent alert returns False."""
    assert engine.resolve_alert("fake-id") is False


def test_analyze_batch(engine: ComplianceEngine) -> None:
    """Batch analysis processes multiple transfers."""
    transfers = [
        _make_transfer(amount=5000.0),
        _make_transfer(amount=100.0),
        _make_transfer(sender="0.0.6666"),
    ]
    alerts = engine.analyze_batch(transfers)
    assert len(alerts) >= 2  # At least large transfer + sanctioned
