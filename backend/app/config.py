"""Application configuration from environment variables."""
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://nseapp:changeme_use_strong_password@localhost:5432/nse_analysis"

    # Security
    secret_key: str = "changeme_generate_with_openssl_rand_hex_32"
    allowed_origins: str = "http://localhost:3000"

    # Data Provider
    default_provider: str = "yahoo"
    broker_api_key: Optional[str] = None
    broker_api_secret: Optional[str] = None
    broker_provider: Optional[str] = None

    # Market
    market_timezone: str = "Asia/Kolkata"
    market_open: str = "09:15"
    market_close: str = "15:30"

    # Worker
    quote_refresh_minutes: int = 5
    candle_update_hour: int = 18
    fundamentals_update_day: str = "saturday"

    # Logging
    log_level: str = "INFO"

    # Optional LLM
    ollama_base_url: Optional[str] = None
    ollama_model: Optional[str] = None

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
