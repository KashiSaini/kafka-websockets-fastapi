from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    project_name: str = Field(default="live-crypto-stream", alias="PROJECT_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    admin_api_key: str = Field(default="change-me-admin-key", alias="ADMIN_API_KEY")
    user_api_key: str = Field(default="change-me-user-key", alias="USER_API_KEY")

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@postgres:5432/market_data",
        alias="DATABASE_URL",
    )

    kafka_bootstrap_servers: str = Field(default="kafka:9092", alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_client_id: str = Field(default="market-app", alias="KAFKA_CLIENT_ID")
    kafka_topic_trades: str = Field(default="market.binance.trades", alias="KAFKA_TOPIC_TRADES")
    kafka_topic_klines: str = Field(default="market.binance.klines", alias="KAFKA_TOPIC_KLINES")
    kafka_consumer_group: str = Field(default="market-consumer-group", alias="KAFKA_CONSUMER_GROUP")

    binance_ws_base: str = Field(
        default="wss://data-stream.binance.vision/stream?streams=",
        alias="BINANCE_WS_BASE",
    )
    tracked_symbols_raw: str = Field(default="btcusdt,ethusdt,bnbusdt", alias="TRACKED_SYMBOLS")
    candle_interval: str = Field(default="1m", alias="CANDLE_INTERVAL")
    ws_push_interval_seconds: float = Field(default=1.0, alias="WS_PUSH_INTERVAL_SECONDS")

    @property
    def tracked_symbols(self) -> list[str]:
        return [item.strip().upper() for item in self.tracked_symbols_raw.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
