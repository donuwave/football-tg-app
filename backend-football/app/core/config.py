from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT_DIR / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True
    backend_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    database_url: str = "sqlite:///./football_tg.db"
    redis_url: str = "redis://localhost:6379/0"

    telegram_bot_token: str = "your_bot_token"
    telegram_channel_id: str = "@your_channel"
    telegram_allowed_user_id: int = 123456789
    telegram_init_data_ttl_seconds: int = 86400

    vk_access_token: str = "your_vk_access_token"
    vk_group_id: str = "your_vk_group_id"
    youtube_client_id: str = "your_youtube_client_id"
    youtube_client_secret: str = "your_youtube_client_secret"
    youtube_refresh_token: str = "your_youtube_refresh_token"
    youtube_channel_id: str = "your_youtube_channel_id"

    local_storage_path: str = "./storage"
    parser_interval_minutes: int = 120
    ai_service_mode: str = "stub"

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
