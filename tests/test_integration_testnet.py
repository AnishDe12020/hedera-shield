"""Integration tests against Hedera testnet mirror node.

These tests hit the real mirror node API (read-only) and verify
our scanner correctly parses live data. They are skipped in CI
unless HEDERA_SHIELD_RUN_INTEGRATION=1 is set.
"""

import os
import pytest
import httpx

from hedera_shield.config import Settings
from hedera_shield.scanner import MirrorNodeScanner

# Skip all tests in this module unless integration flag is set
pytestmark = pytest.mark.skipif(
    os.environ.get("HEDERA_SHIELD_RUN_INTEGRATION", "0") != "1",
    reason="Set HEDERA_SHIELD_RUN_INTEGRATION=1 to run integration tests",
)

TESTNET_MIRROR = "https://testnet.mirrornode.hedera.com"


@pytest.fixture
def testnet_config() -> Settings:
    return Settings(
        hedera_network="testnet",
        mirror_node_url=TESTNET_MIRROR,
        monitored_token_ids=[],
    )


@pytest.fixture
def testnet_scanner(testnet_config: Settings) -> MirrorNodeScanner:
    return MirrorNodeScanner(config=testnet_config)


@pytest.mark.asyncio
async def test_mirror_node_reachable():
    """Verify testnet mirror node is reachable."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{TESTNET_MIRROR}/api/v1/transactions", params={"limit": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert "transactions" in data


@pytest.mark.asyncio
async def test_fetch_recent_transactions():
    """Fetch recent transactions from testnet and verify structure."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{TESTNET_MIRROR}/api/v1/transactions",
            params={"limit": 5, "order": "desc"},
        )
        assert resp.status_code == 200
        data = resp.json()
        txns = data.get("transactions", [])
        assert len(txns) > 0

        tx = txns[0]
        assert "transaction_id" in tx
        assert "consensus_timestamp" in tx
        assert "transfers" in tx  # HBAR transfers


@pytest.mark.asyncio
async def test_fetch_account_info():
    """Fetch info for the treasury account (0.0.2)."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{TESTNET_MIRROR}/api/v1/accounts/0.0.2")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("account") == "0.0.2"


@pytest.mark.asyncio
async def test_scanner_parse_live_data(testnet_scanner: MirrorNodeScanner):
    """Scanner should handle real mirror node responses without crashing."""
    client = await testnet_scanner._get_client()
    resp = await client.get(
        f"{TESTNET_MIRROR}/api/v1/transactions",
        params={"limit": 10, "order": "desc"},
    )
    data = resp.json()
    # Parse with a dummy token ID - should return empty (no token transfers for random token)
    transfers = testnet_scanner._parse_transactions(data, "0.0.99999999")
    assert isinstance(transfers, list)
    await testnet_scanner.close()


@pytest.mark.asyncio
async def test_fetch_token_info():
    """Fetch token info from testnet."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{TESTNET_MIRROR}/api/v1/tokens",
            params={"limit": 3, "order": "desc"},
        )
        assert resp.status_code == 200
        data = resp.json()
        tokens = data.get("tokens", [])
        # Testnet should have tokens
        assert isinstance(tokens, list)


@pytest.mark.asyncio
async def test_network_info():
    """Fetch network info to verify API versioning."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{TESTNET_MIRROR}/api/v1/network/supply")
        assert resp.status_code == 200
        data = resp.json()
        assert "released_supply" in data or "total_supply" in data
