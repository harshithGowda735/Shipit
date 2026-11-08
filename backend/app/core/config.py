from pathlib import Path

from pydantic import PositiveInt, SecretStr, field_validator
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
    SECRET_KEY: SecretStr
    ACCESS_TOKEN_EXPIRE_MINUTES: PositiveInt = 30

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, secret: SecretStr) -> SecretStr:
        if len(secret.get_secret_value().encode("utf-8")) < 32:
            raise ValueError("SECRET_KEY must be at least 32 bytes")
        return secret


settings = Settings()
