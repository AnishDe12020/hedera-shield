"""Scanner module — connects to Hedera mirror node REST API, monitors token transfers."""

import asyncio
import logging
from datetime import datetime, timezone

import httpx

from hedera_shield.config import Settings, settings
from hedera_shield.models import TokenTransfer

logger = logging.getLogger(__name__)


class MirrorNodeScanner:
    """Polls the Hedera Mirror Node API for token transfers and parses them."""

    def __init__(self, config: Settings | None = None) -> None:
        self.config = config or settings
        self.base_url = self.config.mirror_node_base_url
        self._last_timestamp: str | None = None
        self._running = False
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def fetch_token_transfers(
        self, token_id: str, limit: int = 100, timestamp_gt: str | None = None
    ) -> list[TokenTransfer]:
        """Fetch recent token transfers from the mirror node."""
        client = await self._get_client()
        url = f"{self.base_url}/tokens/{token_id}/balances"
        # Use transactions endpoint for transfer history
        tx_url = f"{self.base_url}/transactions"
        params: dict[str, str | int] = {
            "transactiontype": "CRYPTOTRANSFER",
            "limit": limit,
            "order": "desc",
        }
        if timestamp_gt:
            params["timestamp"] = f"gt:{timestamp_gt}"

        try:
            response = await client.get(tx_url, params=params)
            response.raise_for_status()
            data = response.json()
            return self._parse_transactions(data, token_id)
        except httpx.HTTPError as e:
            logger.error("Failed to fetch transfers for token %s: %s", token_id, e)
            return []

    def _parse_transactions(self, data: dict, token_id: str) -> list[TokenTransfer]:
        """Parse mirror node API response into TokenTransfer objects."""
        transfers: list[TokenTransfer] = []
        for tx in data.get("transactions", []):
            token_transfers = tx.get("token_transfers", [])
            senders = [t for t in token_transfers if t.get("token_id") == token_id and t.get("amount", 0) < 0]
            receivers = [t for t in token_transfers if t.get("token_id") == token_id and t.get("amount", 0) > 0]

            for sender in senders:
                for receiver in receivers:
                    transfers.append(
                        TokenTransfer(
                            transaction_id=tx.get("transaction_id", ""),
                            token_id=token_id,
                            sender=sender.get("account", ""),
                            receiver=receiver.get("account", ""),
                            amount=abs(receiver.get("amount", 0)),
                            timestamp=datetime.fromtimestamp(
                                float(tx.get("consensus_timestamp", "0")), tz=timezone.utc
                            ),
                            memo=tx.get("memo_base64", ""),
                        )
                    )
        return transfers

    async def scan_all_tokens(self) -> list[TokenTransfer]:
        """Scan all monitored tokens for new transfers."""
        all_transfers: list[TokenTransfer] = []
        for token_id in self.config.monitored_token_ids:
            transfers = await self.fetch_token_transfers(
                token_id, timestamp_gt=self._last_timestamp
            )
            all_transfers.extend(transfers)
            logger.info("Found %d transfers for token %s", len(transfers), token_id)

        if all_transfers:
            latest = max(t.timestamp for t in all_transfers)
            self._last_timestamp = str(latest.timestamp())

        return all_transfers

    async def run(self, callback=None) -> None:
        """Continuously poll for new transfers."""
        self._running = True
        logger.info("Scanner started — monitoring %d tokens", len(self.config.monitored_token_ids))

        while self._running:
            try:
                transfers = await self.scan_all_tokens()
                if transfers and callback:
                    await callback(transfers)
            except Exception:
                logger.exception("Error during scan cycle")

            await asyncio.sleep(self.config.mirror_node_poll_interval)

    def stop(self) -> None:
        self._running = False
        logger.info("Scanner stopped")
