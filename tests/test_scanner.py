"""Tests for the mirror node scanner with mocked HTTP responses."""

import pytest
import httpx

from hedera_shield.config import Settings
from hedera_shield.scanner import MirrorNodeScanner


MOCK_TRANSACTIONS_RESPONSE = {
    "transactions": [
        {
            "transaction_id": "0.0.1234-1700000000-000000000",
            "consensus_timestamp": "1700000000.000000000",
            "memo_base64": "",
            "token_transfers": [
                {"token_id": "0.0.5555", "account": "0.0.1111", "amount": -500},
                {"token_id": "0.0.5555", "account": "0.0.2222", "amount": 500},
            ],
        },
        {
            "transaction_id": "0.0.1234-1700001000-000000000",
            "consensus_timestamp": "1700001000.000000000",
            "memo_base64": "dGVzdA==",
            "token_transfers": [
                {"token_id": "0.0.5555", "account": "0.0.3333", "amount": -10000},
                {"token_id": "0.0.5555", "account": "0.0.4444", "amount": 10000},
            ],
        },
    ]
}

EMPTY_RESPONSE = {"transactions": []}


@pytest.fixture
def config() -> Settings:
    return Settings(
        hedera_network="testnet",
        mirror_node_url="https://testnet.mirrornode.hedera.com",
        monitored_token_ids=["0.0.5555"],
    )


@pytest.fixture
def scanner(config: Settings) -> MirrorNodeScanner:
    return MirrorNodeScanner(config=config)


@pytest.mark.asyncio
async def test_parse_transactions(scanner: MirrorNodeScanner) -> None:
    """Test that mirror node responses are parsed into TokenTransfer objects."""
    transfers = scanner._parse_transactions(MOCK_TRANSACTIONS_RESPONSE, "0.0.5555")

    assert len(transfers) == 2
    assert transfers[0].sender == "0.0.1111"
    assert transfers[0].receiver == "0.0.2222"
    assert transfers[0].amount == 500
    assert transfers[0].token_id == "0.0.5555"

    assert transfers[1].sender == "0.0.3333"
    assert transfers[1].receiver == "0.0.4444"
    assert transfers[1].amount == 10000


@pytest.mark.asyncio
async def test_parse_empty_response(scanner: MirrorNodeScanner) -> None:
    """Test parsing an empty response."""
    transfers = scanner._parse_transactions(EMPTY_RESPONSE, "0.0.5555")
    assert transfers == []


@pytest.mark.asyncio
async def test_parse_ignores_other_tokens(scanner: MirrorNodeScanner) -> None:
    """Test that transfers for other tokens are ignored."""
    data = {
        "transactions": [
            {
                "transaction_id": "tx-1",
                "consensus_timestamp": "1700000000.000000000",
                "memo_base64": "",
                "token_transfers": [
                    {"token_id": "0.0.9999", "account": "0.0.1111", "amount": -100},
                    {"token_id": "0.0.9999", "account": "0.0.2222", "amount": 100},
                ],
            }
        ]
    }
    transfers = scanner._parse_transactions(data, "0.0.5555")
    assert transfers == []


@pytest.mark.asyncio
async def test_fetch_transfers_http_error(scanner: MirrorNodeScanner, monkeypatch) -> None:
    """Test that HTTP errors are handled gracefully."""

    async def mock_request(*args, **kwargs):
        raise httpx.HTTPStatusError(
            "Server Error",
            request=httpx.Request("GET", "https://example.com"),
            response=httpx.Response(500),
        )

    # Create a mock client
    client = httpx.AsyncClient()
    monkeypatch.setattr(client, "request", mock_request)
    scanner._client = client
    scanner.max_retries = 1

    transfers = await scanner.fetch_token_transfers("0.0.5555")
    assert transfers == []

    await scanner.close()


@pytest.mark.asyncio
async def test_scan_all_tokens_updates_timestamp(scanner: MirrorNodeScanner, monkeypatch) -> None:
    """Test that scan_all_tokens updates the last timestamp."""

    async def mock_fetch(token_id, limit=100, timestamp_gt=None):
        return scanner._parse_transactions(MOCK_TRANSACTIONS_RESPONSE, token_id)

    monkeypatch.setattr(scanner, "fetch_token_transfers", mock_fetch)

    transfers = await scanner.scan_all_tokens()
    assert len(transfers) == 2
    assert scanner._last_timestamp is not None


def test_stop(scanner: MirrorNodeScanner) -> None:
    """Test that stop sets the running flag."""
    scanner._running = True
    scanner.stop()
    assert scanner._running is False
