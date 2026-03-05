"""Tests for the new compliance rules: structuring, dormant account, cross-token wash."""

import pytest
from datetime import datetime, timedelta, timezone

from hedera_shield.config import Settings
from hedera_shield.compliance import ComplianceEngine
from hedera_shield.models import (
    AlertType,
    ComplianceRule,
    EnforcementAction,
    Severity,
    TokenTransfer,
)


def _make_transfer(
    sender: str = "0.0.1111",
    receiver: str = "0.0.2222",
    amount: float = 100.0,
    token_id: str = "0.0.5555",
    timestamp: datetime | None = None,
) -> TokenTransfer:
    return TokenTransfer(
        transaction_id="tx-test-001",
        token_id=token_id,
        sender=sender,
        receiver=receiver,
        amount=amount,
        timestamp=timestamp or datetime.now(timezone.utc),
    )


# =============================================================================
# Structuring Detection Tests
# =============================================================================


class TestStructuringDetection:
    def _engine_with_structuring(self) -> ComplianceEngine:
        config = Settings(large_transfer_threshold=10000.0)
        engine = ComplianceEngine(config=config)
        engine.rules = [
            ComplianceRule(
                id="rule-structuring",
                name="Structuring",
                description="Detect structuring",
                alert_type=AlertType.STRUCTURING,
                severity=Severity.HIGH,
                enabled=True,
                parameters={
                    "window_seconds": 7200,
                    "min_count": 3,
                    "threshold_pct": 0.9,
                    "recommended_action": "freeze",
                },
            )
        ]
        return engine

    def test_structuring_detected(self) -> None:
        """Three transfers just below threshold should trigger structuring alert."""
        engine = self._engine_with_structuring()
        now = datetime.now(timezone.utc)

        alerts = []
        # Send 3 transfers at 9500 (just below 10000 threshold, above 9000 = 90%)
        for i in range(3):
            t = _make_transfer(sender="0.0.3333", amount=9500.0, timestamp=now)
            t.transaction_id = f"tx-struct-{i}"
            alerts.extend(engine.analyze(t))

        struct_alerts = [a for a in alerts if a.alert_type == AlertType.STRUCTURING]
        assert len(struct_alerts) >= 1
        assert "structuring" in struct_alerts[0].description.lower()

    def test_no_structuring_below_range(self) -> None:
        """Transfers well below the threshold should not trigger structuring."""
        engine = self._engine_with_structuring()

        alerts = []
        for i in range(5):
            t = _make_transfer(sender="0.0.4444", amount=1000.0)
            t.transaction_id = f"tx-low-{i}"
            alerts.extend(engine.analyze(t))

        struct_alerts = [a for a in alerts if a.alert_type == AlertType.STRUCTURING]
        assert len(struct_alerts) == 0

    def test_no_structuring_above_threshold(self) -> None:
        """Transfers at or above threshold trigger large_transfer, not structuring."""
        engine = self._engine_with_structuring()

        alerts = []
        for i in range(3):
            t = _make_transfer(sender="0.0.5555", amount=10000.0)
            t.transaction_id = f"tx-above-{i}"
            alerts.extend(engine.analyze(t))

        struct_alerts = [a for a in alerts if a.alert_type == AlertType.STRUCTURING]
        assert len(struct_alerts) == 0


# =============================================================================
# Dormant Account Tests
# =============================================================================


class TestDormantAccountDetection:
    def _engine_with_dormant(self) -> ComplianceEngine:
        config = Settings(large_transfer_threshold=10000.0)
        engine = ComplianceEngine(config=config)
        engine.rules = [
            ComplianceRule(
                id="rule-dormant",
                name="Dormant Account",
                description="Detect dormant",
                alert_type=AlertType.DORMANT_ACCOUNT,
                severity=Severity.MEDIUM,
                enabled=True,
                parameters={
                    "dormancy_seconds": 86400,  # 1 day for testing
                    "min_amount": 500.0,
                    "recommended_action": "kyc_revoke",
                },
            )
        ]
        return engine

    def test_dormant_account_triggers_on_reactivation(self) -> None:
        """Account dormant for >1 day then making large transfer should alert."""
        engine = self._engine_with_dormant()

        # First transfer sets the last-seen timestamp
        old_time = datetime.now(timezone.utc) - timedelta(days=2)
        t1 = _make_transfer(sender="0.0.7777", amount=100.0, timestamp=old_time)
        engine.analyze(t1)

        # Manually set the last-seen to 2 days ago
        engine._account_last_seen["0.0.7777"] = old_time

        # New transfer now — should trigger dormant alert
        t2 = _make_transfer(sender="0.0.7777", amount=5000.0)
        alerts = engine.analyze(t2)

        dormant_alerts = [a for a in alerts if a.alert_type == AlertType.DORMANT_ACCOUNT]
        assert len(dormant_alerts) == 1
        assert "dormant" in dormant_alerts[0].description.lower()

    def test_active_account_no_dormant_alert(self) -> None:
        """Recently active account should not trigger dormant alert."""
        engine = self._engine_with_dormant()

        t1 = _make_transfer(sender="0.0.8888", amount=1000.0)
        engine.analyze(t1)

        t2 = _make_transfer(sender="0.0.8888", amount=5000.0)
        alerts = engine.analyze(t2)

        dormant_alerts = [a for a in alerts if a.alert_type == AlertType.DORMANT_ACCOUNT]
        assert len(dormant_alerts) == 0

    def test_dormant_small_amount_no_alert(self) -> None:
        """Dormant account making small transfer should not alert."""
        engine = self._engine_with_dormant()
        old_time = datetime.now(timezone.utc) - timedelta(days=5)
        engine._account_last_seen["0.0.9999"] = old_time

        t = _make_transfer(sender="0.0.9999", amount=100.0)  # Below min_amount
        alerts = engine.analyze(t)

        dormant_alerts = [a for a in alerts if a.alert_type == AlertType.DORMANT_ACCOUNT]
        assert len(dormant_alerts) == 0


# =============================================================================
# Cross-Token Wash Trading Tests
# =============================================================================


class TestCrossTokenWashTrading:
    def _engine_with_wash(self) -> ComplianceEngine:
        config = Settings(large_transfer_threshold=10000.0)
        engine = ComplianceEngine(config=config)
        engine.rules = [
            ComplianceRule(
                id="rule-wash",
                name="Cross-Token Wash",
                description="Detect wash trading",
                alert_type=AlertType.CROSS_TOKEN_WASH,
                severity=Severity.HIGH,
                enabled=True,
                parameters={
                    "window_seconds": 3600,
                    "min_tokens": 3,
                    "recommended_action": "freeze",
                },
            )
        ]
        return engine

    def test_wash_trading_detected(self) -> None:
        """Same pair across 3 tokens should trigger wash alert."""
        engine = self._engine_with_wash()

        alerts = []
        for i, token in enumerate(["0.0.1001", "0.0.1002", "0.0.1003"]):
            t = _make_transfer(
                sender="0.0.AAAA",
                receiver="0.0.BBBB",
                amount=500.0,
                token_id=token,
            )
            t.transaction_id = f"tx-wash-{i}"
            alerts.extend(engine.analyze(t))

        wash_alerts = [a for a in alerts if a.alert_type == AlertType.CROSS_TOKEN_WASH]
        assert len(wash_alerts) >= 1
        assert "wash" in wash_alerts[0].description.lower()

    def test_same_token_no_wash_alert(self) -> None:
        """Same pair with same token should not trigger wash alert."""
        engine = self._engine_with_wash()

        alerts = []
        for i in range(5):
            t = _make_transfer(
                sender="0.0.CCCC",
                receiver="0.0.DDDD",
                amount=500.0,
                token_id="0.0.5555",
            )
            t.transaction_id = f"tx-same-{i}"
            alerts.extend(engine.analyze(t))

        wash_alerts = [a for a in alerts if a.alert_type == AlertType.CROSS_TOKEN_WASH]
        assert len(wash_alerts) == 0

    def test_different_pairs_no_wash_alert(self) -> None:
        """Different sender/receiver pairs across tokens should not trigger."""
        engine = self._engine_with_wash()

        alerts = []
        for i, (sender, receiver, token) in enumerate([
            ("0.0.A1", "0.0.B1", "0.0.1001"),
            ("0.0.A2", "0.0.B2", "0.0.1002"),
            ("0.0.A3", "0.0.B3", "0.0.1003"),
        ]):
            t = _make_transfer(sender=sender, receiver=receiver, token_id=token)
            t.transaction_id = f"tx-diff-{i}"
            alerts.extend(engine.analyze(t))

        wash_alerts = [a for a in alerts if a.alert_type == AlertType.CROSS_TOKEN_WASH]
        assert len(wash_alerts) == 0


# =============================================================================
# HCS Reporter Tests
# =============================================================================


class TestHCSReporter:
    @pytest.mark.asyncio
    async def test_dry_run_publish(self) -> None:
        from hedera_shield.hcs_reporter import HCSReporter

        reporter = HCSReporter(topic_id="0.0.12345", dry_run=True)
        transfer = _make_transfer(amount=50000.0)
        from hedera_shield.models import Alert

        alert = Alert(
            id="alert-hcs-test",
            alert_type=AlertType.LARGE_TRANSFER,
            severity=Severity.HIGH,
            transaction=transfer,
            description="Test alert for HCS",
            risk_score=0.8,
        )

        result = await reporter.publish_alert(alert)
        assert result["status"] == "dry_run"
        assert result["alert_id"] == "alert-hcs-test"
        assert result["topic_id"] == "0.0.12345"
        assert len(reporter.published_messages) == 1

    @pytest.mark.asyncio
    async def test_batch_publish(self) -> None:
        from hedera_shield.hcs_reporter import HCSReporter
        from hedera_shield.models import Alert

        reporter = HCSReporter(topic_id="0.0.12345", dry_run=True)

        alerts = []
        for i in range(3):
            transfer = _make_transfer(amount=50000.0 + i)
            alerts.append(
                Alert(
                    id=f"alert-batch-{i}",
                    alert_type=AlertType.LARGE_TRANSFER,
                    severity=Severity.HIGH,
                    transaction=transfer,
                    description=f"Batch alert {i}",
                    risk_score=0.7,
                )
            )

        results = await reporter.publish_batch(alerts)
        assert len(results) == 3
        assert all(r["status"] == "dry_run" for r in results)

    @pytest.mark.asyncio
    async def test_serialize_alert(self) -> None:
        from hedera_shield.hcs_reporter import HCSReporter
        from hedera_shield.models import Alert

        reporter = HCSReporter(topic_id="0.0.99999", dry_run=True)
        transfer = _make_transfer(sender="0.0.AAA", receiver="0.0.BBB", amount=25000.0)
        alert = Alert(
            id="alert-ser-001",
            alert_type=AlertType.SANCTIONED_ADDRESS,
            severity=Severity.CRITICAL,
            transaction=transfer,
            description="Sanctioned address detected",
            risk_score=1.0,
            recommended_action=EnforcementAction.FREEZE,
        )

        data = reporter._serialize_alert(alert)
        assert data["alert_id"] == "alert-ser-001"
        assert data["alert_type"] == "sanctioned_address"
        assert data["severity"] == "critical"
        assert data["sender"] == "0.0.AAA"
        assert data["recommended_action"] == "freeze"


# =============================================================================
# YAML-loaded rules integration
# =============================================================================


class TestYAMLRulesIntegration:
    def test_yaml_rules_load_all_eight(self) -> None:
        """Loading rules from YAML should produce all 8 rule types."""
        config = Settings(large_transfer_threshold=10000.0)
        engine = ComplianceEngine(config=config, rules_config_path="auto")

        rule_ids = {r.id for r in engine.rules}
        assert "rule-structuring" in rule_ids
        assert "rule-dormant-account" in rule_ids
        assert "rule-cross-token-wash" in rule_ids
        assert "rule-large-transfer" in rule_ids
        assert "rule-rapid-succession" in rule_ids

    def test_yaml_rules_all_enabled(self) -> None:
        """All rules from YAML config should be enabled."""
        config = Settings(large_transfer_threshold=10000.0)
        engine = ComplianceEngine(config=config, rules_config_path="auto")

        for rule in engine.rules:
            assert rule.enabled, f"Rule {rule.id} should be enabled"
