"""Scanner module — connects to Hedera mirror node REST API, monitors token and HBAR transfers."""

import asyncio
import logging
from datetime import datetime, timezone

import httpx

from hedera_shield.config import Settings, settings
from hedera_shield.models import (
    AccountTokenBalance,
    HbarTransfer,
    NftTransfer,
    TokenTransfer,
)

logger = logging.getLogger(__name__)

# Retry configuration defaults
_DEFAULT_MAX_RETRIES = 3
_DEFAULT_BACKOFF_BASE = 1.0
_DEFAULT_BACKOFF_FACTOR = 2.0
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class MirrorNodeScanner:
    """Polls the Hedera Mirror Node API for token transfers, HBAR transfers, and NFTs."""

    def __init__(self, config: Settings | None = None) -> None:
        self.config = config or settings
        self.base_url = self.config.mirror_node_base_url
        self._last_timestamp: str | None = None
        self._running = False
        self._client: httpx.AsyncClient | None = None
        self.max_retries = _DEFAULT_MAX_RETRIES
        self.backoff_base = _DEFAULT_BACKOFF_BASE
        self.backoff_factor = _DEFAULT_BACKOFF_FACTOR

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ------------------------------------------------------------------
    # Retry helper with exponential backoff
    # ------------------------------------------------------------------

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        params: dict | None = None,
    ) -> httpx.Response:
        """Execute an HTTP request with exponential backoff on transient failures.

        Raises the underlying ``httpx.HTTPError`` after all retries are
        exhausted so callers can handle it.
        """
        client = await self._get_client()
        last_exc: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(
                    "HTTP %s %s attempt %d/%d",
                    method.upper(),
                    url,
                    attempt,
                    self.max_retries,
                )
                response = await client.request(method, url, params=params)

                # Retry on transient server / rate-limit errors
                if response.status_code in _RETRYABLE_STATUS_CODES:
                    logger.warning(
                        "Received %d from %s (attempt %d/%d)",
                        response.status_code,
                        url,
                        attempt,
                        self.max_retries,
                    )
                    if attempt < self.max_retries:
                        delay = self.backoff_base * (self.backoff_factor ** (attempt - 1))
                        await asyncio.sleep(delay)
                        continue
                    # Final attempt — raise so the caller sees the error
                    response.raise_for_status()

                response.raise_for_status()
                return response

            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    delay = self.backoff_base * (self.backoff_factor ** (attempt - 1))
                    logger.warning(
                        "Request to %s failed (attempt %d/%d): %s — retrying in %.1fs",
                        url,
                        attempt,
                        self.max_retries,
                        exc,
                        delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        "Request to %s failed after %d attempts: %s",
                        url,
                        self.max_retries,
                        exc,
                    )

        # Should not normally reach here, but satisfy the type checker.
        raise last_exc  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Pagination helper
    # ------------------------------------------------------------------

    async def _fetch_all_pages(
        self,
        url: str,
        params: dict[str, str | int] | None = None,
        *,
        max_pages: int = 10,
    ) -> list[dict]:
        """Follow ``links.next`` across pages and return all raw JSON bodies."""
        pages: list[dict] = []
        current_url = url
        current_params = dict(params) if params else None

        for page_num in range(1, max_pages + 1):
            logger.debug("Fetching page %d: %s", page_num, current_url)
            response = await self._request_with_retry(
                "GET", current_url, params=current_params
            )
            data = response.json()
            pages.append(data)

            # Mirror node pagination: links.next is a relative or absolute URL
            next_link = (data.get("links") or {}).get("next")
            if not next_link:
                break

            # The next link is a full path with query params — resolve it
            if next_link.startswith("http"):
                current_url = next_link
            else:
                # Relative path from mirror node (e.g. "/api/v1/transactions?...")
                base = self.base_url.split("/api/v1")[0]
                current_url = base + next_link

            # Params are baked into the next link URL, so clear them
            current_params = None

        logger.info("Fetched %d page(s) from %s", len(pages), url)
        return pages

    # ------------------------------------------------------------------
    # Token transfers (existing, enhanced with pagination + retry)
    # ------------------------------------------------------------------

    async def fetch_token_transfers(
        self, token_id: str, limit: int = 100, timestamp_gt: str | None = None
    ) -> list[TokenTransfer]:
        """Fetch recent token transfers from the mirror node."""
        tx_url = f"{self.base_url}/transactions"
        params: dict[str, str | int] = {
            "transactiontype": "CRYPTOTRANSFER",
            "limit": limit,
            "order": "desc",
        }
        if timestamp_gt:
            params["timestamp"] = f"gt:{timestamp_gt}"

        logger.info("Fetching token transfers for %s (after=%s)", token_id, timestamp_gt)

        try:
            pages = await self._fetch_all_pages(tx_url, params, max_pages=5)
            transfers: list[TokenTransfer] = []
            for data in pages:
                transfers.extend(self._parse_transactions(data, token_id))
            logger.info(
                "Parsed %d token transfers for %s across %d page(s)",
                len(transfers),
                token_id,
                len(pages),
            )
            return transfers
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

    # ------------------------------------------------------------------
    # HBAR transfer monitoring
    # ------------------------------------------------------------------

    async def fetch_hbar_transfers(
        self,
        limit: int = 100,
        timestamp_gt: str | None = None,
        account_id: str | None = None,
    ) -> list[HbarTransfer]:
        """Fetch HBAR (crypto) transfers from /api/v1/transactions.

        Unlike token transfers, HBAR movements live in the ``transfers``
        array of each transaction (not ``token_transfers``).
        """
        tx_url = f"{self.base_url}/transactions"
        params: dict[str, str | int] = {
            "transactiontype": "CRYPTOTRANSFER",
            "limit": limit,
            "order": "desc",
        }
        if timestamp_gt:
            params["timestamp"] = f"gt:{timestamp_gt}"
        if account_id:
            params["account.id"] = account_id

        logger.info(
            "Fetching HBAR transfers (account=%s, after=%s)", account_id, timestamp_gt
        )

        try:
            pages = await self._fetch_all_pages(tx_url, params, max_pages=5)
            hbar_transfers: list[HbarTransfer] = []
            for data in pages:
                hbar_transfers.extend(self._parse_hbar_transfers(data))
            logger.info("Parsed %d HBAR transfers across %d page(s)", len(hbar_transfers), len(pages))
            return hbar_transfers
        except httpx.HTTPError as e:
            logger.error("Failed to fetch HBAR transfers: %s", e)
            return []

    @staticmethod
    def _parse_hbar_transfers(data: dict) -> list[HbarTransfer]:
        """Parse HBAR transfers from the ``transfers`` array in each transaction."""
        results: list[HbarTransfer] = []
        for tx in data.get("transactions", []):
            transfers = tx.get("transfers", [])
            senders = [t for t in transfers if t.get("amount", 0) < 0]
            receivers = [t for t in transfers if t.get("amount", 0) > 0]

            for sender in senders:
                for receiver in receivers:
                    results.append(
                        HbarTransfer(
                            transaction_id=tx.get("transaction_id", ""),
                            sender=sender.get("account", ""),
                            receiver=receiver.get("account", ""),
                            amount=abs(receiver.get("amount", 0)),
                            timestamp=datetime.fromtimestamp(
                                float(tx.get("consensus_timestamp", "0")),
                                tz=timezone.utc,
                            ),
                            memo=tx.get("memo_base64", ""),
                        )
                    )
        return results

    # ------------------------------------------------------------------
    # NFT transfer detection
    # ------------------------------------------------------------------

    async def fetch_nft_transfers(
        self,
        token_id: str | None = None,
        limit: int = 100,
        timestamp_gt: str | None = None,
    ) -> list[NftTransfer]:
        """Fetch NFT transfers from the mirror node.

        Scans the ``nft_transfers`` array present in CRYPTOTRANSFER
        transactions.  Optionally filters by *token_id*.
        """
        tx_url = f"{self.base_url}/transactions"
        params: dict[str, str | int] = {
            "transactiontype": "CRYPTOTRANSFER",
            "limit": limit,
            "order": "desc",
        }
        if timestamp_gt:
            params["timestamp"] = f"gt:{timestamp_gt}"

        logger.info(
            "Fetching NFT transfers (token=%s, after=%s)", token_id, timestamp_gt
        )

        try:
            pages = await self._fetch_all_pages(tx_url, params, max_pages=5)
            nft_transfers: list[NftTransfer] = []
            for data in pages:
                nft_transfers.extend(self._parse_nft_transfers(data, token_id))
            logger.info(
                "Parsed %d NFT transfers across %d page(s)",
                len(nft_transfers),
                len(pages),
            )
            return nft_transfers
        except httpx.HTTPError as e:
            logger.error("Failed to fetch NFT transfers: %s", e)
            return []

    @staticmethod
    def _parse_nft_transfers(
        data: dict, token_id: str | None = None
    ) -> list[NftTransfer]:
        """Parse ``nft_transfers`` from transaction data."""
        results: list[NftTransfer] = []
        for tx in data.get("transactions", []):
            for nft in tx.get("nft_transfers", []):
                if token_id and nft.get("token_id") != token_id:
                    continue
                results.append(
                    NftTransfer(
                        transaction_id=tx.get("transaction_id", ""),
                        token_id=nft.get("token_id", ""),
                        serial_number=nft.get("serial_number", 0),
                        sender=nft.get("sender_account_id", ""),
                        receiver=nft.get("receiver_account_id", ""),
                        timestamp=datetime.fromtimestamp(
                            float(tx.get("consensus_timestamp", "0")),
                            tz=timezone.utc,
                        ),
                        memo=tx.get("memo_base64", ""),
                    )
                )
        return results

    # ------------------------------------------------------------------
    # Account balance checking
    # ------------------------------------------------------------------

    async def fetch_account_token_balances(
        self, account_id: str
    ) -> list[AccountTokenBalance]:
        """Fetch token balances for *account_id* via
        ``/api/v1/accounts/{accountId}/tokens``.
        """
        url = f"{self.base_url}/accounts/{account_id}/tokens"
        logger.info("Fetching token balances for account %s", account_id)

        try:
            pages = await self._fetch_all_pages(url, max_pages=5)
            balances: list[AccountTokenBalance] = []
            for data in pages:
                for entry in data.get("tokens", []):
                    balances.append(
                        AccountTokenBalance(
                            token_id=entry.get("token_id", ""),
                            balance=entry.get("balance", 0),
                            decimals=entry.get("decimals", 0),
                        )
                    )
            logger.info(
                "Found %d token balances for account %s", len(balances), account_id
            )
            return balances
        except httpx.HTTPError as e:
            logger.error(
                "Failed to fetch token balances for account %s: %s", account_id, e
            )
            return []

    # ------------------------------------------------------------------
    # Transaction detail fetching
    # ------------------------------------------------------------------

    async def fetch_transaction_detail(self, transaction_id: str) -> dict | None:
        """Fetch full details for a single transaction via
        ``/api/v1/transactions/{transactionId}``.

        Returns the raw JSON dict (first transaction entry) or ``None``
        on failure.
        """
        url = f"{self.base_url}/transactions/{transaction_id}"
        logger.info("Fetching detail for transaction %s", transaction_id)

        try:
            response = await self._request_with_retry("GET", url)
            data = response.json()
            transactions = data.get("transactions", [])
            if transactions:
                logger.debug("Transaction %s detail retrieved", transaction_id)
                return transactions[0]
            logger.warning("No transaction data found for %s", transaction_id)
            return None
        except httpx.HTTPError as e:
            logger.error(
                "Failed to fetch transaction %s: %s", transaction_id, e
            )
            return None

    # ------------------------------------------------------------------
    # Scanning loop (existing, preserved)
    # ------------------------------------------------------------------

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
