"""Compliance engine -- rule-based transaction analysis with configurable thresholds."""

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from hedera_shield.config import Settings, settings
from hedera_shield.models import (
    Alert,
    AlertType,
    ComplianceRule,
    EnforcementAction,
    Severity,
    TokenTransfer,
)
from hedera_shield.rules_config import load_rules_config, load_sanctions_list

logger = logging.getLogger(__name__)

# Maps YAML rule section names to AlertType values
_ALERT_TYPE_MAP: dict[str, AlertType] = {
    "large_transfer": AlertType.LARGE_TRANSFER,
    "velocity": AlertType.VELOCITY_BREACH,
    "sanctions": AlertType.SANCTIONED_ADDRESS,
    "round_number": AlertType.ROUND_NUMBER,
    "rapid_succession": AlertType.RAPID_SUCCESSION,
    "structuring": AlertType.STRUCTURING,
    "dormant_account": AlertType.DORMANT_ACCOUNT,
    "cross_token_wash": AlertType.CROSS_TOKEN_WASH,
}

# Maps string action names to EnforcementAction enum values
_ACTION_MAP: dict[str, EnforcementAction] = {
    "freeze": EnforcementAction.FREEZE,
    "wipe": EnforcementAction.WIPE,
    "kyc_revoke": EnforcementAction.KYC_REVOKE,
    "pause": EnforcementAction.PAUSE,
    "none": EnforcementAction.NONE,
}

# Maps string severity names to Severity enum values
_SEVERITY_MAP: dict[str, Severity] = {
    "low": Severity.LOW,
    "medium": Severity.MEDIUM,
    "high": Severity.HIGH,
    "critical": Severity.CRITICAL,
}


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


def _build_rules_from_config(rules_cfg: dict[str, Any]) -> list[ComplianceRule]:
    """Build ComplianceRule list from a loaded rules configuration dict."""
    rules: list[ComplianceRule] = []

    section_meta = {
        "large_transfer": ("rule-large-transfer", "Large Transfer Detection",
                           "Flags transfers exceeding the configured threshold"),
        "velocity": ("rule-velocity", "Velocity Check",
                     "Flags accounts with excessive transfer frequency"),
        "sanctions": ("rule-sanctioned", "Sanctioned Address Match",
                      "Flags interactions with known sanctioned addresses"),
        "round_number": ("rule-round-number", "Round Number Detection",
                         "Flags suspiciously round-number transfers"),
        "rapid_succession": ("rule-rapid-succession", "Rapid Succession Detection",
                             "Flags multiple transfers from the same sender within seconds"),
        "structuring": ("rule-structuring", "Structuring Detection",
                        "Detects structured transfers just below thresholds to evade detection"),
        "dormant_account": ("rule-dormant-account", "Dormant Account Activation",
                            "Flags large transfers from accounts with no recent activity"),
        "cross_token_wash": ("rule-cross-token-wash", "Cross-Token Wash Trading",
                             "Detects circular flows between the same accounts across tokens"),
    }

    for section_key, (rule_id, name, description) in section_meta.items():
        section = rules_cfg.get(section_key, {})
        if not section:
            continue

        alert_type = _ALERT_TYPE_MAP.get(section_key)
        if alert_type is None:
            continue

        severity = _SEVERITY_MAP.get(
            str(section.get("severity", "medium")).lower(), Severity.MEDIUM
        )
        enabled = bool(section.get("enabled", True))

        rules.append(
            ComplianceRule(
                id=rule_id,
                name=name,
                description=description,
                alert_type=alert_type,
                severity=severity,
                enabled=enabled,
                parameters=dict(section),
            )
        )

    return rules


class ComplianceEngine:
    """Rule-based compliance engine for analyzing token transfers.

    Parameters
    ----------
    config : Settings | None
        Application settings.  Falls back to the module-level ``settings``
        singleton when *None*.
    rules_config_path : str | None
        Explicit path to a YAML/JSON rules file.  When provided the engine
        loads rules from that file.  When *None* (the default) the engine
        uses the hardcoded ``DEFAULT_RULES`` for full backward compatibility.
        Pass the string ``"auto"`` to auto-discover ``config/rules.yaml``
        relative to the project root.
    """

    def __init__(
        self,
        config: Settings | None = None,
        rules_config_path: str | None = None,
    ) -> None:
        self.config = config or settings

        # Only load YAML rules when the caller explicitly opts in.
        self._use_yaml = rules_config_path is not None
        if self._use_yaml:
            path = None if rules_config_path == "auto" else rules_config_path
            self._rules_cfg: dict[str, Any] = load_rules_config(path)
            yaml_rules = _build_rules_from_config(self._rules_cfg)
            self.rules: list[ComplianceRule] = yaml_rules if yaml_rules else [
                r.model_copy() for r in DEFAULT_RULES
            ]
        else:
            self._rules_cfg = {}
            self.rules = [r.model_copy() for r in DEFAULT_RULES]

        # Optional calibration for risk scores loaded from YAML config.
        self._risk_calibration = self._rules_cfg.get("risk_score_calibration", {})

        self.alerts: list[Alert] = []
        self._transfer_history: defaultdict[str, list[datetime]] = defaultdict(list)
        self._rapid_history: defaultdict[str, list[datetime]] = defaultdict(list)
        # Structuring: track transfer amounts per sender in a rolling window
        self._structuring_history: defaultdict[str, list[tuple[datetime, float]]] = defaultdict(list)
        # Dormant account: track last-seen activity timestamp per account
        self._account_last_seen: dict[str, datetime] = {}
        # Cross-token wash: track (sender, receiver) pairs across token IDs
        self._wash_history: defaultdict[tuple[str, str], list[tuple[datetime, str]]] = defaultdict(list)

        # Load sanctions set: merge YAML-configured addresses with Settings addresses
        sanctions_cfg = self._rules_cfg.get("sanctions", {})
        self._sanctions: set[str] = load_sanctions_list(sanctions_cfg)
        # Also include any addresses from the Settings object
        if self.config.sanctioned_addresses:
            self._sanctions.update(self.config.sanctioned_addresses)

    # -- Public API (unchanged) ------------------------------------------------

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
            elif rule.alert_type == AlertType.ROUND_NUMBER:
                alert = self._check_round_number(transfer, rule)
            elif rule.alert_type == AlertType.RAPID_SUCCESSION:
                alert = self._check_rapid_succession(transfer, rule)

            if rule.alert_type == AlertType.STRUCTURING:
                alert = self._check_structuring(transfer, rule)
            elif rule.alert_type == AlertType.DORMANT_ACCOUNT:
                alert = self._check_dormant_account(transfer, rule)
            elif rule.alert_type == AlertType.CROSS_TOKEN_WASH:
                alert = self._check_cross_token_wash(transfer, rule)

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

    # -- Rule implementations --------------------------------------------------

    def _get_rule_param(self, rule: ComplianceRule, key: str, default: Any = None) -> Any:
        """Get a parameter from the rule's parameters dict (sourced from YAML)."""
        return rule.parameters.get(key, default)

    def _get_recommended_action(self, rule: ComplianceRule) -> EnforcementAction:
        """Resolve the recommended enforcement action from rule parameters."""
        action_str = str(self._get_rule_param(rule, "recommended_action", "freeze")).lower()
        return _ACTION_MAP.get(action_str, EnforcementAction.FREEZE)

    def _calibrate_risk_score(self, alert_type: AlertType, base_score: float) -> float:
        """Apply optional calibration settings to a base risk score.

        Expected YAML shape:
        risk_score_calibration:
          default: {multiplier: 1.0, offset: 0.0, min: 0.0, max: 1.0}
          by_alert_type:
            large_transfer: {multiplier: 1.2, max: 0.95}
        """
        cfg = self._risk_calibration or {}
        default_cfg = cfg.get("default", {})
        by_type = cfg.get("by_alert_type", {})
        type_cfg = by_type.get(alert_type.value, {})

        multiplier = float(type_cfg.get("multiplier", default_cfg.get("multiplier", 1.0)))
        offset = float(type_cfg.get("offset", default_cfg.get("offset", 0.0)))
        min_score = float(type_cfg.get("min", default_cfg.get("min", 0.0)))
        max_score = float(type_cfg.get("max", default_cfg.get("max", 1.0)))
        if min_score > max_score:
            min_score, max_score = max_score, min_score

        calibrated = (base_score * multiplier) + offset
        calibrated = max(min_score, min(max_score, calibrated))
        return max(0.0, min(1.0, calibrated))

    def _check_large_transfer(self, transfer: TokenTransfer, rule: ComplianceRule) -> Alert | None:
        # Per-token threshold from YAML config takes highest priority,
        # then Settings threshold, then YAML default_threshold as last resort.
        token_thresholds = self._get_rule_param(rule, "token_thresholds", {})
        if transfer.token_id in token_thresholds:
            threshold = float(token_thresholds[transfer.token_id])
        else:
            threshold = self.config.large_transfer_threshold

        if transfer.amount >= threshold:
            base_score = min(transfer.amount / (threshold * 10), 1.0)
            return self._create_alert(
                alert_type=AlertType.LARGE_TRANSFER,
                severity=rule.severity,
                transaction=transfer,
                description=f"Transfer of {transfer.amount} exceeds threshold of {threshold}",
                risk_score=self._calibrate_risk_score(AlertType.LARGE_TRANSFER, base_score),
                recommended_action=self._get_recommended_action(rule),
            )
        return None

    def _check_velocity(self, transfer: TokenTransfer, rule: ComplianceRule) -> Alert | None:
        now = datetime.now(timezone.utc)

        # Check for per-token overrides
        token_overrides = self._get_rule_param(rule, "token_overrides", {})
        if transfer.token_id in token_overrides:
            override = token_overrides[transfer.token_id]
            window_secs = int(override.get("window_seconds", self.config.velocity_window_seconds))
            max_transfers = int(override.get("max_transfers", self.config.velocity_max_transfers))
        else:
            # Settings values take priority over YAML defaults
            window_secs = self.config.velocity_window_seconds
            max_transfers = self.config.velocity_max_transfers

        window = timedelta(seconds=window_secs)
        sender = transfer.sender

        self._transfer_history[sender].append(transfer.timestamp)
        # Prune old entries
        self._transfer_history[sender] = [
            ts for ts in self._transfer_history[sender] if now - ts < window
        ]

        count = len(self._transfer_history[sender])
        if count >= max_transfers:
            base_score = min(count / (max_transfers * 2), 1.0)
            return self._create_alert(
                alert_type=AlertType.VELOCITY_BREACH,
                severity=rule.severity,
                transaction=transfer,
                description=f"Account {sender} made {count} transfers in {window_secs}s window",
                risk_score=self._calibrate_risk_score(AlertType.VELOCITY_BREACH, base_score),
                recommended_action=self._get_recommended_action(rule),
            )
        return None

    def _check_sanctioned(self, transfer: TokenTransfer, rule: ComplianceRule) -> Alert | None:
        flagged = None
        if transfer.sender in self._sanctions:
            flagged = transfer.sender
        elif transfer.receiver in self._sanctions:
            flagged = transfer.receiver

        if flagged:
            base_score = 1.0
            return self._create_alert(
                alert_type=AlertType.SANCTIONED_ADDRESS,
                severity=Severity.CRITICAL,
                transaction=transfer,
                description=f"Transaction involves sanctioned address: {flagged}",
                risk_score=self._calibrate_risk_score(AlertType.SANCTIONED_ADDRESS, base_score),
                recommended_action=self._get_recommended_action(rule),
            )
        return None

    def _check_round_number(self, transfer: TokenTransfer, rule: ComplianceRule) -> Alert | None:
        """Flag transfers with suspiciously round amounts."""
        minimum_amount = float(self._get_rule_param(rule, "minimum_amount", 1000.0))
        divisors = self._get_rule_param(rule, "divisors", [50000.0, 10000.0, 5000.0, 1000.0])

        if transfer.amount < minimum_amount:
            return None

        for divisor in sorted(divisors, reverse=True):
            divisor = float(divisor)
            if divisor > 0 and transfer.amount % divisor == 0:
                base_score = min(transfer.amount / (divisor * 10), 1.0)
                return self._create_alert(
                    alert_type=AlertType.ROUND_NUMBER,
                    severity=rule.severity,
                    transaction=transfer,
                    description=(
                        f"Suspicious round-number transfer: {transfer.amount} "
                        f"(divisible by {divisor})"
                    ),
                    risk_score=self._calibrate_risk_score(AlertType.ROUND_NUMBER, base_score),
                    recommended_action=self._get_recommended_action(rule),
                )

        return None

    def _check_rapid_succession(self, transfer: TokenTransfer, rule: ComplianceRule) -> Alert | None:
        """Flag multiple transfers from the same sender within seconds."""
        window_secs = int(self._get_rule_param(rule, "window_seconds", 10))
        min_transfers = int(self._get_rule_param(rule, "min_transfers", 3))

        now = datetime.now(timezone.utc)
        window = timedelta(seconds=window_secs)
        sender = transfer.sender

        self._rapid_history[sender].append(transfer.timestamp)
        # Prune old entries
        self._rapid_history[sender] = [
            ts for ts in self._rapid_history[sender] if now - ts < window
        ]

        count = len(self._rapid_history[sender])
        if count >= min_transfers:
            base_score = min(count / (min_transfers * 3), 1.0)
            return self._create_alert(
                alert_type=AlertType.RAPID_SUCCESSION,
                severity=rule.severity,
                transaction=transfer,
                description=(
                    f"Rapid succession: {count} transfers from {sender} "
                    f"within {window_secs}s"
                ),
                risk_score=self._calibrate_risk_score(AlertType.RAPID_SUCCESSION, base_score),
                recommended_action=self._get_recommended_action(rule),
            )
        return None

    def _check_structuring(self, transfer: TokenTransfer, rule: ComplianceRule) -> Alert | None:
        """Detect structuring: multiple transfers just below the large-transfer threshold.

        Structuring (a.k.a. "smurfing") is a common AML evasion technique where
        a sender breaks a large transfer into multiple smaller ones, each just
        below the reporting threshold.
        """
        window_secs = int(self._get_rule_param(rule, "window_seconds", 7200))
        min_count = int(self._get_rule_param(rule, "min_count", 3))
        # Use 90% of large-transfer threshold as the "just below" boundary
        pct = float(self._get_rule_param(rule, "threshold_pct", 0.9))
        base_threshold = self.config.large_transfer_threshold
        just_below = base_threshold * pct

        now = datetime.now(timezone.utc)
        window = timedelta(seconds=window_secs)
        sender = transfer.sender

        self._structuring_history[sender].append((transfer.timestamp, transfer.amount))
        # Prune old entries
        self._structuring_history[sender] = [
            (ts, amt) for ts, amt in self._structuring_history[sender]
            if now - ts < window
        ]

        # Count transfers that are between just_below and the threshold
        suspicious = [
            (ts, amt) for ts, amt in self._structuring_history[sender]
            if just_below <= amt < base_threshold
        ]

        if len(suspicious) >= min_count:
            total = sum(amt for _, amt in suspicious)
            base_score = min(len(suspicious) / (min_count * 3), 1.0)
            return self._create_alert(
                alert_type=AlertType.STRUCTURING,
                severity=rule.severity,
                transaction=transfer,
                description=(
                    f"Suspected structuring: {len(suspicious)} transfers from {sender} "
                    f"just below threshold ({just_below:.0f}-{base_threshold:.0f}), "
                    f"totaling {total:.0f}"
                ),
                risk_score=self._calibrate_risk_score(AlertType.STRUCTURING, base_score),
                recommended_action=self._get_recommended_action(rule),
            )
        return None

    def _check_dormant_account(self, transfer: TokenTransfer, rule: ComplianceRule) -> Alert | None:
        """Flag transfers from accounts that were dormant (no activity for a long period).

        Suddenly active dormant accounts are a common indicator of compromised
        or sleeper accounts used for money laundering.
        """
        dormancy_seconds = int(self._get_rule_param(rule, "dormancy_seconds", 86400 * 30))
        min_amount = float(self._get_rule_param(rule, "min_amount", 1000.0))

        sender = transfer.sender
        now = datetime.now(timezone.utc)

        if sender in self._account_last_seen:
            last_seen = self._account_last_seen[sender]
            gap = (now - last_seen).total_seconds()

            if gap >= dormancy_seconds and transfer.amount >= min_amount:
                self._account_last_seen[sender] = now
                days = int(gap / 86400)
                base_score = min(gap / (dormancy_seconds * 3), 1.0)
                return self._create_alert(
                    alert_type=AlertType.DORMANT_ACCOUNT,
                    severity=rule.severity,
                    transaction=transfer,
                    description=(
                        f"Dormant account reactivation: {sender} was inactive for "
                        f"{days} days, now transferring {transfer.amount}"
                    ),
                    risk_score=self._calibrate_risk_score(AlertType.DORMANT_ACCOUNT, base_score),
                    recommended_action=self._get_recommended_action(rule),
                )

        # Record activity
        self._account_last_seen[sender] = now
        return None

    def _check_cross_token_wash(self, transfer: TokenTransfer, rule: ComplianceRule) -> Alert | None:
        """Detect wash trading across multiple token IDs between the same pair of accounts.

        If accounts A→B appear with multiple different token IDs in a short
        window, it may indicate wash trading or layering across tokens.
        """
        window_secs = int(self._get_rule_param(rule, "window_seconds", 3600))
        min_tokens = int(self._get_rule_param(rule, "min_tokens", 3))

        now = datetime.now(timezone.utc)
        window = timedelta(seconds=window_secs)
        pair = (transfer.sender, transfer.receiver)

        self._wash_history[pair].append((transfer.timestamp, transfer.token_id))
        # Prune old entries
        self._wash_history[pair] = [
            (ts, tid) for ts, tid in self._wash_history[pair]
            if now - ts < window
        ]

        unique_tokens = set(tid for _, tid in self._wash_history[pair])
        if len(unique_tokens) >= min_tokens:
            base_score = min(len(unique_tokens) / (min_tokens * 2), 1.0)
            return self._create_alert(
                alert_type=AlertType.CROSS_TOKEN_WASH,
                severity=rule.severity,
                transaction=transfer,
                description=(
                    f"Cross-token wash trading: {transfer.sender} → {transfer.receiver} "
                    f"across {len(unique_tokens)} different tokens in {window_secs}s"
                ),
                risk_score=self._calibrate_risk_score(AlertType.CROSS_TOKEN_WASH, base_score),
                recommended_action=self._get_recommended_action(rule),
            )
        return None

    # -- Helpers ---------------------------------------------------------------

    def _create_alert(self, **kwargs: Any) -> Alert:
        alert = Alert(id=f"alert-{uuid.uuid4().hex[:8]}", **kwargs)
        logger.warning("Alert generated: [%s] %s", alert.alert_type.value, alert.description)
        return alert
