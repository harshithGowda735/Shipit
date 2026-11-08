from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ENV_FILE = BACKEND_ROOT.parent / ".env"
ENV_FILE = (
    PROJECT_ENV_FILE
    if PROJECT_ENV_FILE.is_file()
    else BACKEND_ROOT / ".env"
)


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
