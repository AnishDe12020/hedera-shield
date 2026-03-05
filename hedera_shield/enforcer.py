"""Enforcer module — executes HTS token operations (freeze, wipe, KYC revoke)."""

import logging
from dataclasses import dataclass
from enum import Enum

from hedera_shield.config import Settings, settings
from hedera_shield.models import EnforcementAction

logger = logging.getLogger(__name__)


class EnforcementStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    DRY_RUN = "dry_run"


@dataclass
class EnforcementResult:
    action: EnforcementAction
    target_account: str
    token_id: str
    status: EnforcementStatus
    transaction_id: str = ""
    error: str = ""


class TokenEnforcer:
    """Executes enforcement actions on HTS tokens.

    In production, this integrates with the Hedera SDK to submit freeze/wipe/KYC
    transactions. For safety, defaults to dry-run mode.
    """

    def __init__(self, config: Settings | None = None, dry_run: bool = True) -> None:
        self.config = config or settings
        self.dry_run = dry_run
        self._client = None
        self.action_log: list[EnforcementResult] = []

    def _get_hedera_client(self):
        """Initialize Hedera SDK client. Requires hedera-sdk package."""
        if self._client is not None:
            return self._client

        try:
            # Dynamic import — hedera-sdk is optional for testing
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
            logger.warning("hedera-sdk not installed — enforcement actions will be dry-run only")
            self.dry_run = True
            return None

    async def freeze_account(self, token_id: str, account_id: str) -> EnforcementResult:
        """Freeze a token for a specific account."""
        if self.dry_run:
            return self._dry_run_result(EnforcementAction.FREEZE, account_id, token_id)

        try:
            from hedera import TokenFreezeTransaction, AccountId, TokenId  # type: ignore[import-untyped]

            client = self._get_hedera_client()
            tx = (
                TokenFreezeTransaction()
                .setTokenId(TokenId.fromString(token_id))
                .setAccountId(AccountId.fromString(account_id))
            )
            response = await self._execute_async(tx, client)
            result = EnforcementResult(
                action=EnforcementAction.FREEZE,
                target_account=account_id,
                token_id=token_id,
                status=EnforcementStatus.SUCCESS,
                transaction_id=str(response.transactionId),
            )
        except Exception as e:
            logger.error("Failed to freeze %s for token %s: %s", account_id, token_id, e)
            result = EnforcementResult(
                action=EnforcementAction.FREEZE,
                target_account=account_id,
                token_id=token_id,
                status=EnforcementStatus.FAILED,
                error=str(e),
            )

        self.action_log.append(result)
        return result

    async def wipe_tokens(self, token_id: str, account_id: str, amount: int) -> EnforcementResult:
        """Wipe tokens from a specific account."""
        if self.dry_run:
            return self._dry_run_result(EnforcementAction.WIPE, account_id, token_id)

        try:
            from hedera import TokenWipeTransaction, AccountId, TokenId  # type: ignore[import-untyped]

            client = self._get_hedera_client()
            tx = (
                TokenWipeTransaction()
                .setTokenId(TokenId.fromString(token_id))
                .setAccountId(AccountId.fromString(account_id))
                .setAmount(amount)
            )
            response = await self._execute_async(tx, client)
            result = EnforcementResult(
                action=EnforcementAction.WIPE,
                target_account=account_id,
                token_id=token_id,
                status=EnforcementStatus.SUCCESS,
                transaction_id=str(response.transactionId),
            )
        except Exception as e:
            logger.error("Failed to wipe tokens from %s: %s", account_id, e)
            result = EnforcementResult(
                action=EnforcementAction.WIPE,
                target_account=account_id,
                token_id=token_id,
                status=EnforcementStatus.FAILED,
                error=str(e),
            )

        self.action_log.append(result)
        return result

    async def revoke_kyc(self, token_id: str, account_id: str) -> EnforcementResult:
        """Revoke KYC status for an account on a token."""
        if self.dry_run:
            return self._dry_run_result(EnforcementAction.KYC_REVOKE, account_id, token_id)

        try:
            from hedera import TokenRevokeKycTransaction, AccountId, TokenId  # type: ignore[import-untyped]

            client = self._get_hedera_client()
            tx = (
                TokenRevokeKycTransaction()
                .setTokenId(TokenId.fromString(token_id))
                .setAccountId(AccountId.fromString(account_id))
            )
            response = await self._execute_async(tx, client)
            result = EnforcementResult(
                action=EnforcementAction.KYC_REVOKE,
                target_account=account_id,
                token_id=token_id,
                status=EnforcementStatus.SUCCESS,
                transaction_id=str(response.transactionId),
            )
        except Exception as e:
            logger.error("Failed to revoke KYC for %s: %s", account_id, e)
            result = EnforcementResult(
                action=EnforcementAction.KYC_REVOKE,
                target_account=account_id,
                token_id=token_id,
                status=EnforcementStatus.FAILED,
                error=str(e),
            )

        self.action_log.append(result)
        return result

    async def enforce(self, action: EnforcementAction, token_id: str, account_id: str) -> EnforcementResult:
        """Execute an enforcement action based on type."""
        if action == EnforcementAction.FREEZE:
            return await self.freeze_account(token_id, account_id)
        elif action == EnforcementAction.WIPE:
            return await self.wipe_tokens(token_id, account_id, 0)
        elif action == EnforcementAction.KYC_REVOKE:
            return await self.revoke_kyc(token_id, account_id)
        else:
            return EnforcementResult(
                action=action,
                target_account=account_id,
                token_id=token_id,
                status=EnforcementStatus.SUCCESS,
            )

    def _dry_run_result(self, action: EnforcementAction, account_id: str, token_id: str) -> EnforcementResult:
        result = EnforcementResult(
            action=action,
            target_account=account_id,
            token_id=token_id,
            status=EnforcementStatus.DRY_RUN,
        )
        logger.info("DRY RUN: %s on account %s for token %s", action.value, account_id, token_id)
        self.action_log.append(result)
        return result

    @staticmethod
    async def _execute_async(tx, client):
        """Execute a Hedera transaction. Wraps sync SDK call."""
        return tx.execute(client)
