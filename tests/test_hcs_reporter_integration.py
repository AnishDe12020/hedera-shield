"""Integration-style HCS reporter tests with fully mocked dependencies."""

import base64
import json
import sys
import types
from datetime import datetime, timezone

import pytest

from hedera_shield.config import Settings
from hedera_shield.hcs_reporter import HCSReporter
from hedera_shield.models import Alert, AlertType, EnforcementAction, Severity, TokenTransfer


def _make_alert(alert_id: str = "alert-hcs-001") -> Alert:
    transfer = TokenTransfer(
        transaction_id="tx-hcs-001",
        token_id="0.0.5555",
        sender="0.0.1111",
        receiver="0.0.2222",
        amount=1234.0,
        timestamp=datetime.now(timezone.utc),
    )
    return Alert(
        id=alert_id,
        alert_type=AlertType.LARGE_TRANSFER,
        severity=Severity.HIGH,
        transaction=transfer,
        description="HCS integration test alert",
        risk_score=0.8,
        recommended_action=EnforcementAction.FREEZE,
    )


def _install_fake_hedera_module(monkeypatch, fail_on_execute: bool = False) -> None:
    fake_hedera = types.ModuleType("hedera")

    class Client:
        @staticmethod
        def forMainnet():
            return Client()

        @staticmethod
        def forTestnet():
            return Client()

        @staticmethod
        def forPreviewnet():
            return Client()

        def setOperator(self, _account_id, _private_key):
            return None

    class AccountId:
        @staticmethod
        def fromString(value: str):
            return value

    class PrivateKey:
        @staticmethod
        def fromString(value: str):
            return value

    class TopicId:
        @staticmethod
        def fromString(value: str):
            return value

    class Receipt:
        topicSequenceNumber = 42

    class TxResponse:
        transactionId = "0.0.1001@1700000000.000000000"

        def getReceipt(self, _client):
            return Receipt()

    class TopicMessageSubmitTransaction:
        def setTopicId(self, _topic_id):
            return self

        def setMessage(self, _message):
            return self

        def execute(self, _client):
            if fail_on_execute:
                raise RuntimeError("submit failed")
            return TxResponse()

    fake_hedera.Client = Client
    fake_hedera.AccountId = AccountId
    fake_hedera.PrivateKey = PrivateKey
    fake_hedera.TopicId = TopicId
    fake_hedera.TopicMessageSubmitTransaction = TopicMessageSubmitTransaction

    monkeypatch.setitem(sys.modules, "hedera", fake_hedera)


@pytest.mark.asyncio
async def test_publish_alert_success_with_mocked_hedera_sdk(monkeypatch) -> None:
    _install_fake_hedera_module(monkeypatch, fail_on_execute=False)

    reporter = HCSReporter(
        config=Settings(hedera_network="testnet"),
        topic_id="0.0.12345",
        dry_run=False,
    )
    result = await reporter.publish_alert(_make_alert())

    assert result["status"] == "success"
    assert result["topic_id"] == "0.0.12345"
    assert result["sequence_number"] == 42
    assert "transaction_id" in result
    assert len(reporter.published_messages) == 1


@pytest.mark.asyncio
async def test_publish_alert_error_with_mocked_hedera_sdk(monkeypatch) -> None:
    _install_fake_hedera_module(monkeypatch, fail_on_execute=True)

    reporter = HCSReporter(
        config=Settings(hedera_network="testnet"),
        topic_id="0.0.12345",
        dry_run=False,
    )
    result = await reporter.publish_alert(_make_alert("alert-hcs-fail"))

    assert result["status"] == "error"
    assert result["alert_id"] == "alert-hcs-fail"
    assert "submit failed" in result["error"]
    assert len(reporter.published_messages) == 1


@pytest.mark.asyncio
async def test_fetch_topic_messages_decodes_and_falls_back_raw(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            valid_payload = base64.b64encode(
                json.dumps({"alert_id": "alert-1", "risk_score": 0.9}).encode()
            ).decode()
            return {
                "messages": [
                    {
                        "message": valid_payload,
                        "consensus_timestamp": "1700000000.000000001",
                        "sequence_number": 10,
                    },
                    {
                        "message": "not-base64",
                        "consensus_timestamp": "1700000000.000000002",
                        "sequence_number": 11,
                    },
                ]
            }

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            return None

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, _url, params=None):
            assert params["limit"] == 2
            assert params["order"] == "desc"
            return FakeResponse()

    import httpx

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    reporter = HCSReporter(
        config=Settings(mirror_node_url="https://testnet.mirrornode.hedera.com"),
        topic_id="0.0.12345",
        dry_run=True,
    )
    messages = await reporter.fetch_topic_messages(limit=2)

    assert len(messages) == 2
    assert messages[0]["alert_id"] == "alert-1"
    assert messages[0]["_sequence_number"] == 10
    assert messages[1]["raw"] == "not-base64"
