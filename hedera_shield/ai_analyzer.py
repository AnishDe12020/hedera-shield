"""AI-powered transaction analysis using Claude for risk scoring and natural language insights."""

import json
import logging

from hedera_shield.config import Settings, settings
from hedera_shield.models import (
    EnforcementAction,
    RiskAssessment,
    Severity,
    TokenTransfer,
)

logger = logging.getLogger(__name__)

RISK_ANALYSIS_PROMPT = """\
You are a blockchain compliance analyst. Analyze the following Hedera token transfer for suspicious activity.

Transaction details:
- Transaction ID: {transaction_id}
- Token ID: {token_id}
- Sender: {sender}
- Receiver: {receiver}
- Amount: {amount}
- Timestamp: {timestamp}
- Memo: {memo}

Additional context:
{context}

Respond with a JSON object containing:
- "risk_score": float between 0.0 (safe) and 1.0 (highly suspicious)
- "risk_level": one of "low", "medium", "high", "critical"
- "reasoning": brief explanation of your assessment
- "recommended_action": one of "none", "freeze", "wipe", "kyc_revoke"
- "flags": list of specific risk indicators found

Respond ONLY with valid JSON, no markdown."""


class AIAnalyzer:
    """Uses Claude to perform intelligent risk analysis on token transfers."""

    def __init__(self, config: Settings | None = None) -> None:
        self.config = config or settings
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client

        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.config.anthropic_api_key)
            return self._client
        except ImportError:
            logger.error("anthropic package not installed")
            return None

    async def analyze_transfer(
        self, transfer: TokenTransfer, context: str = ""
    ) -> RiskAssessment:
        """Analyze a single transfer using Claude."""
        client = self._get_client()
        if not client:
            return self._fallback_assessment()

        prompt = RISK_ANALYSIS_PROMPT.format(
            transaction_id=transfer.transaction_id,
            token_id=transfer.token_id,
            sender=transfer.sender,
            receiver=transfer.receiver,
            amount=transfer.amount,
            timestamp=transfer.timestamp.isoformat(),
            memo=transfer.memo,
            context=context or "No additional context provided.",
        )

        try:
            message = client.messages.create(
                model=self.config.ai_model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            response_text = message.content[0].text
            return self._parse_response(response_text)
        except Exception as e:
            logger.error("AI analysis failed: %s", e)
            return self._fallback_assessment()

    async def analyze_batch(
        self, transfers: list[TokenTransfer], context: str = ""
    ) -> list[RiskAssessment]:
        """Analyze multiple transfers."""
        results = []
        for transfer in transfers:
            assessment = await self.analyze_transfer(transfer, context)
            results.append(assessment)
        return results

    def _parse_response(self, text: str) -> RiskAssessment:
        """Parse Claude's JSON response into a RiskAssessment."""
        try:
            data = json.loads(text)
            action_map = {
                "none": EnforcementAction.NONE,
                "freeze": EnforcementAction.FREEZE,
                "wipe": EnforcementAction.WIPE,
                "kyc_revoke": EnforcementAction.KYC_REVOKE,
            }
            severity_map = {
                "low": Severity.LOW,
                "medium": Severity.MEDIUM,
                "high": Severity.HIGH,
                "critical": Severity.CRITICAL,
            }
            return RiskAssessment(
                risk_score=float(data.get("risk_score", 0.5)),
                risk_level=severity_map.get(data.get("risk_level", "medium"), Severity.MEDIUM),
                reasoning=data.get("reasoning", ""),
                recommended_action=action_map.get(
                    data.get("recommended_action", "none"), EnforcementAction.NONE
                ),
                flags=data.get("flags", []),
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error("Failed to parse AI response: %s", e)
            return self._fallback_assessment()

    @staticmethod
    def _fallback_assessment() -> RiskAssessment:
        return RiskAssessment(
            risk_score=0.5,
            risk_level=Severity.MEDIUM,
            reasoning="AI analysis unavailable — manual review recommended",
            recommended_action=EnforcementAction.NONE,
            flags=["ai_unavailable"],
        )
