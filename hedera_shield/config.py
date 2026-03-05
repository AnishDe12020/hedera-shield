"""Environment-based configuration for HederaShield."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Hedera network
    hedera_network: str = Field(default="testnet", description="Hedera network: mainnet, testnet, previewnet")
    hedera_operator_id: str = Field(default="", description="Hedera operator account ID")
    hedera_operator_key: str = Field(default="", description="Hedera operator private key")

    # Mirror node
    mirror_node_url: str = Field(default="https://testnet.mirrornode.hedera.com")
    mirror_node_poll_interval: int = Field(default=10, description="Polling interval in seconds")

    # AI
    anthropic_api_key: str = Field(default="", description="Anthropic API key for Claude")
    ai_model: str = Field(default="claude-sonnet-4-20250514", description="Claude model to use")

    # Compliance thresholds
    large_transfer_threshold: float = Field(default=10000.0, description="Flag transfers above this amount")
    velocity_window_seconds: int = Field(default=3600, description="Time window for velocity checks")
    velocity_max_transfers: int = Field(default=50, description="Max transfers in velocity window")

    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)

    # Monitored tokens
    monitored_token_ids: list[str] = Field(default_factory=list, description="Token IDs to monitor")

    # Sanctioned addresses
    sanctioned_addresses: list[str] = Field(default_factory=list, description="Known sanctioned addresses")

    model_config = {"env_prefix": "HEDERA_SHIELD_", "env_file": ".env", "extra": "ignore"}

    @property
    def mirror_node_base_url(self) -> str:
        return self.mirror_node_url.rstrip("/") + "/api/v1"


settings = Settings()
