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
    # Se true e IA configurada, correção de respostas usa API (economia: max_tokens baixo no código)
    use_ai_correction: bool = True

    # Upload PDF (caminho relativo ao cwd do app, ex. dentro do container /app)
    upload_dir: str = "uploads"
    max_pdf_bytes: int = 15 * 1024 * 1024
    max_extracted_chars: int = 200_000
    min_extracted_chars: int = 80
    ocr_languages: str = "eng+por"
    default_deck_size: int = 8
    max_deck_size: int = 20


@lru_cache
def get_settings() -> Settings:
    return Settings()
