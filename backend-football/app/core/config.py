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
    telegram_channel_url: str | None = None
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
    parser_max_item_age_hours: int = 24
    ai_service_mode: str = "stub"
    ai_ollama_base_url: str = "http://host.docker.internal:11434"
    ai_ollama_model: str = "qwen2.5:3b"
    ai_request_timeout_seconds: int = 90
    ai_ollama_keep_alive: str = "10m"
    ai_ollama_temperature: float = 0.35
    ai_ollama_top_p: float = 0.9
    translation_service_mode: str = "google"
    translation_target_language: str = "ru"
    ai_system_prompt: str = (
        "Ты редактор футбольного Telegram-канала. "
        "Сделай из новости короткий факт для Telegram-канала на русском языке. "
        "Финальный ответ должен быть только на русском языке. "
        "Если исходный материал на английском или другом языке, переведи смысл на русский. "
        "Пиши ясно, плотно и без воды. Не выдумывай факты. "
        "Обычно это 1-2 предложения и один главный факт. "
        "Не добавляй вводные фразы вроде 'Вот пост' или 'Конечно'."
    )

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
