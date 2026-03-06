"""Tests for risk-score calibration config behavior."""

import json
from datetime import datetime, timezone

from hedera_shield.compliance import ComplianceEngine
from hedera_shield.config import Settings
from hedera_shield.models import AlertType, TokenTransfer


def _make_transfer(amount: float, sender: str = "0.0.1111") -> TokenTransfer:
    return TokenTransfer(
        transaction_id="tx-risk-001",
        token_id="0.0.5555",
        sender=sender,
        receiver="0.0.2222",
        amount=amount,
        timestamp=datetime.now(timezone.utc),
    )


def test_risk_score_default_passthrough_without_yaml() -> None:
    """Default engine behavior should keep base score unchanged."""
    engine = ComplianceEngine(config=Settings(large_transfer_threshold=1000.0))
    alerts = engine.analyze(_make_transfer(amount=5000.0))
    large = [a for a in alerts if a.alert_type == AlertType.LARGE_TRANSFER]

    assert len(large) == 1
    assert large[0].risk_score == 0.5


def test_risk_score_calibration_from_yaml(tmp_path) -> None:
    """Configured calibration should scale and clamp base scores."""
    rules_json = tmp_path / "rules.json"
    rules_json.write_text(
        json.dumps(
            {
                "large_transfer": {
                    "enabled": True,
                    "severity": "high",
                    "default_threshold": 1000.0,
                    "token_thresholds": {},
                    "recommended_action": "freeze",
                },
                "velocity": {"enabled": False},
                "sanctions": {"enabled": False},
                "risk_score_calibration": {
                    "default": {
                        "multiplier": 1.0,
                        "offset": 0.0,
                        "min": 0.0,
                        "max": 1.0,
                    },
                    "by_alert_type": {
                        "large_transfer": {
                            "multiplier": 1.5,
                            "offset": 0.1,
                            "min": 0.2,
                            "max": 0.7,
                        }
                    },
                },
            }
        )
    )
    engine = ComplianceEngine(
        config=Settings(large_transfer_threshold=1000.0),
        rules_config_path=str(rules_json),
    )
    alerts = engine.analyze(_make_transfer(amount=5000.0))
    large = [a for a in alerts if a.alert_type == AlertType.LARGE_TRANSFER]

    # Base=0.5 => (0.5 * 1.5) + 0.1 = 0.85 -> clamped to configured max=0.7
    assert len(large) == 1
    assert large[0].risk_score == 0.7
