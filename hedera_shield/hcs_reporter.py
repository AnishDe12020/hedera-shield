"""HCS (Hedera Consensus Service) reporter — publishes compliance alerts as immutable audit logs.

Each alert is serialized to JSON and submitted as an HCS message, creating a
tamper-proof, timestamped compliance audit trail on the Hedera public ledger.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from hedera_shield.config import Settings, settings
from hedera_shield.models import Alert

logger = logging.getLogger(__name__)


class HCSReporter:
    """Publishes compliance alerts to an HCS topic for immutable audit logging.

    Parameters
    ----------
    config : Settings | None
        Application settings.
    topic_id : str
        The HCS topic ID to publish to (e.g. ``"0.0.12345"``).
    dry_run : bool
        When *True* (default), messages are logged but not submitted to Hedera.
    """

    def __init__(
        self,
        config: Settings | None = None,
        topic_id: str = "",
        dry_run: bool = True,
    ) -> None:
        self.config = config or settings
        self.topic_id = topic_id
        self.dry_run = dry_run
        self._client = None
        self.published_messages: list[dict[str, Any]] = []

    def _get_hedera_client(self):
        """Initialize Hedera SDK client for HCS submissions."""
        if self._client is not None:
            return self._client

        try:
            from hedera import Client, AccountId, PrivateKey  # type: ignore[import-untyped]

            if self.config.hedera_network == "mainnet":
                client = Client.forMainnet()
            elif self.config.hedera_network == "testnet":
                client = Client.forTestnet()
            else:
                client = Client.forPreviewnet()

            if self.config.hedera_operator_id and self.config.hedera_operator_key:
                client.setOperator(
                    AccountId.fromString(self.config.hedera_operator_id),
                    PrivateKey.fromString(self.config.hedera_operator_key),
                )
            self._client = client
            return client
        except ImportError:
            logger.warning(
                "hedera-sdk not installed — HCS reporting will be dry-run only"
            )
            self.dry_run = True
            return None

    def _serialize_alert(self, alert: Alert) -> dict[str, Any]:
        """Convert an Alert to a JSON-serializable dict for HCS submission."""
        return {
            "version": "1.0",
            "type": "compliance_alert",
            "alert_id": alert.id,
            "alert_type": alert.alert_type.value,
            "severity": alert.severity.value,
            "risk_score": alert.risk_score,
            "description": alert.description,
            "transaction_id": alert.transaction.transaction_id,
            "token_id": alert.transaction.token_id,
            "sender": alert.transaction.sender,
            "receiver": alert.transaction.receiver,
            "amount": alert.transaction.amount,
            "recommended_action": alert.recommended_action.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def publish_alert(self, alert: Alert) -> dict[str, Any]:
        """Publish a single alert to HCS.

        Returns a result dict with status and optional transaction ID.
        """
        message_data = self._serialize_alert(alert)
        message_json = json.dumps(message_data, separators=(",", ":"))

        if self.dry_run:
            result = {
                "status": "dry_run",
                "topic_id": self.topic_id,
                "alert_id": alert.id,
                "message_size_bytes": len(message_json.encode()),
            }
            logger.info(
                "HCS DRY RUN: Would publish alert %s to topic %s (%d bytes)",
                alert.id,
                self.topic_id,
                len(message_json.encode()),
            )
            self.published_messages.append(result)
            return result

        try:
            from hedera import (  # type: ignore[import-untyped]
                TopicMessageSubmitTransaction,
                TopicId,
            )

            client = self._get_hedera_client()
            if not client:
                return {"status": "error", "error": "No Hedera client available"}

            tx = (
                TopicMessageSubmitTransaction()
                .setTopicId(TopicId.fromString(self.topic_id))
                .setMessage(message_json)
            )
            response = tx.execute(client)
            receipt = response.getReceipt(client)

            result = {
                "status": "success",
                "topic_id": self.topic_id,
                "alert_id": alert.id,
                "sequence_number": receipt.topicSequenceNumber,
                "transaction_id": str(response.transactionId),
            }
            logger.info(
                "HCS: Published alert %s to topic %s (seq: %s)",
                alert.id,
                self.topic_id,
                receipt.topicSequenceNumber,
            )
            self.published_messages.append(result)
            return result

        except Exception as e:
            logger.error("HCS publish failed for alert %s: %s", alert.id, e)
            result = {"status": "error", "alert_id": alert.id, "error": str(e)}
            self.published_messages.append(result)
            return result

    async def publish_batch(self, alerts: list[Alert]) -> list[dict[str, Any]]:
        """Publish multiple alerts to HCS."""
        results = []
        for alert in alerts:
            result = await self.publish_alert(alert)
            results.append(result)
        return results

    async def fetch_topic_messages(
        self, limit: int = 25, sequence_gt: int | None = None
    ) -> list[dict[str, Any]]:
        """Fetch recent HCS messages from the audit topic via Mirror Node.

        This allows the dashboard to display the immutable audit trail.
        """
        import httpx

        url = f"{self.config.mirror_node_base_url}/topics/{self.topic_id}/messages"
        params: dict[str, str | int] = {"limit": limit, "order": "desc"}
        if sequence_gt is not None:
            params["sequencenumber"] = f"gt:{sequence_gt}"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                messages = []
                for msg in data.get("messages", []):
                    try:
                        import base64
                        decoded = base64.b64decode(msg.get("message", "")).decode()
                        parsed = json.loads(decoded)
                        parsed["_consensus_timestamp"] = msg.get(
                            "consensus_timestamp"
                        )
                        parsed["_sequence_number"] = msg.get("sequence_number")
                        messages.append(parsed)
                    except Exception:
                        messages.append(
                            {
                                "raw": msg.get("message", ""),
                                "_consensus_timestamp": msg.get(
                                    "consensus_timestamp"
                                ),
                            }
                        )
                return messages
        except Exception as e:
            logger.error("Failed to fetch HCS messages: %s", e)
            return []
