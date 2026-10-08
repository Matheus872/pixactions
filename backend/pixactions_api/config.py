from decimal import Decimal
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"
    database_url: str = "sqlite+aiosqlite:///./dev.db"
    solana_rpc_url: str = "https://api.devnet.solana.com"
    solana_cluster: str = "devnet"
    service_keypair: str = ""
    mock_usdc_mint: str = ""
    privy_app_id: str = ""
    privy_verification_key: str = ""
    pix_webhook_secret: str = "dev-secret"
    mock_pix_autopay_seconds: int = 8
    mock_brl_per_usd: Decimal = Decimal("5.50")
    pix_expiration_seconds: int = 900
    tx_cache_seconds: int = 45
    public_web_url: str = "http://localhost:3000"
    public_api_url: str = "http://localhost:8000"

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def privy_key_pem(self) -> str:
        return self.privy_verification_key.replace("\\n", "\n")


@lru_cache
def get_settings() -> Settings:
    return Settings()
