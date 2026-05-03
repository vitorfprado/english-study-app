from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "English Study App"
    app_env: str = "development"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/english_study"

    # IA opcional: se vazio, usa fallback local
    ai_provider: str = ""  # openai | anthropic | (vazio = mock)
    ai_api_key: str = ""
    ai_model: str = "gpt-4o-mini"
    ai_base_url: str = ""  # opcional, ex.: proxy OpenAI-compatible


@lru_cache
def get_settings() -> Settings:
    return Settings()
