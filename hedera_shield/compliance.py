"""Compliance engine — rule-based transaction analysis with configurable thresholds."""

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from hedera_shield.config import Settings, settings
from hedera_shield.models import (
    Alert,
    AlertType,
    ComplianceRule,
    EnforcementAction,
    Severity,
    TokenTransfer,
)

logger = logging.getLogger(__name__)


DEFAULT_RULES: list[ComplianceRule] = [
    ComplianceRule(
        id="rule-large-transfer",
        name="Large Transfer Detection",
        description="Flags transfers exceeding the configured threshold",
        alert_type=AlertType.LARGE_TRANSFER,
        severity=Severity.HIGH,
    ),
    ComplianceRule(
        id="rule-velocity",
        name="Velocity Check",
        description="Flags accounts with excessive transfer frequency",
        alert_type=AlertType.VELOCITY_BREACH,
        severity=Severity.MEDIUM,
    ),
    ComplianceRule(
        id="rule-sanctioned",
        name="Sanctioned Address Match",
        description="Flags interactions with known sanctioned addresses",
        alert_type=AlertType.SANCTIONED_ADDRESS,
        severity=Severity.CRITICAL,
    ),
]


class ComplianceEngine:
    """Rule-based compliance engine for analyzing token transfers."""

    def __init__(self, config: Settings | None = None) -> None:
        self.config = config or settings
        self.rules: list[ComplianceRule] = [r.model_copy() for r in DEFAULT_RULES]
        self.alerts: list[Alert] = []
        self._transfer_history: defaultdict[str, list[datetime]] = defaultdict(list)

    def add_rule(self, rule: ComplianceRule) -> None:
        self.rules.append(rule)

    def remove_rule(self, rule_id: str) -> bool:
        before = len(self.rules)
        self.rules = [r for r in self.rules if r.id != rule_id]
        return len(self.rules) < before

    def get_rules(self) -> list[ComplianceRule]:
        return self.rules

    def analyze(self, transfer: TokenTransfer) -> list[Alert]:
        """Run all enabled rules against a transfer. Returns any alerts generated."""
        alerts: list[Alert] = []
        for rule in self.rules:
            if not rule.enabled:
                continue

            alert = None
            if rule.alert_type == AlertType.LARGE_TRANSFER:
                alert = self._check_large_transfer(transfer, rule)
            elif rule.alert_type == AlertType.VELOCITY_BREACH:
                alert = self._check_velocity(transfer, rule)
            elif rule.alert_type == AlertType.SANCTIONED_ADDRESS:
                alert = self._check_sanctioned(transfer, rule)

            if alert:
                alerts.append(alert)

        self.alerts.extend(alerts)
        return alerts

    def analyze_batch(self, transfers: list[TokenTransfer]) -> list[Alert]:
        """Analyze a batch of transfers."""
        all_alerts: list[Alert] = []
        for transfer in transfers:
            all_alerts.extend(self.analyze(transfer))
        return all_alerts

    def _check_large_transfer(self, transfer: TokenTransfer, rule: ComplianceRule) -> Alert | None:
        threshold = self.config.large_transfer_threshold
        if transfer.amount >= threshold:
            return self._create_alert(
                alert_type=AlertType.LARGE_TRANSFER,
                severity=rule.severity,
                transaction=transfer,
                description=f"Transfer of {transfer.amount} exceeds threshold of {threshold}",
                risk_score=min(transfer.amount / (threshold * 10), 1.0),
                recommended_action=EnforcementAction.FREEZE,
            )
        return None

    def _check_velocity(self, transfer: TokenTransfer, rule: ComplianceRule) -> Alert | None:
        now = datetime.now(timezone.utc)
        window = timedelta(seconds=self.config.velocity_window_seconds)
        sender = transfer.sender

        self._transfer_history[sender].append(transfer.timestamp)
        # Prune old entries
        self._transfer_history[sender] = [
            ts for ts in self._transfer_history[sender] if now - ts < window
        ]

        count = len(self._transfer_history[sender])
        if count >= self.config.velocity_max_transfers:
            return self._create_alert(
                alert_type=AlertType.VELOCITY_BREACH,
                severity=rule.severity,
                transaction=transfer,
                description=f"Account {sender} made {count} transfers in {self.config.velocity_window_seconds}s window",
                risk_score=min(count / (self.config.velocity_max_transfers * 2), 1.0),
                recommended_action=EnforcementAction.FREEZE,
            )
        return None

    def _check_sanctioned(self, transfer: TokenTransfer, rule: ComplianceRule) -> Alert | None:
        sanctioned = set(self.config.sanctioned_addresses)
        flagged = None
        if transfer.sender in sanctioned:
            flagged = transfer.sender
        elif transfer.receiver in sanctioned:
            flagged = transfer.receiver

        if flagged:
            return self._create_alert(
                alert_type=AlertType.SANCTIONED_ADDRESS,
                severity=Severity.CRITICAL,
                transaction=transfer,
                description=f"Transaction involves sanctioned address: {flagged}",
                risk_score=1.0,
                recommended_action=EnforcementAction.FREEZE,
            )
        return None

    def _create_alert(self, **kwargs) -> Alert:
        alert = Alert(id=f"alert-{uuid.uuid4().hex[:8]}", **kwargs)
        logger.warning("Alert generated: [%s] %s", alert.alert_type.value, alert.description)
        return alert

    def get_alerts(self, unresolved_only: bool = False) -> list[Alert]:
        if unresolved_only:
            return [a for a in self.alerts if not a.resolved]
        return self.alerts

    def resolve_alert(self, alert_id: str) -> bool:
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.resolved = True
                return True
        return False
