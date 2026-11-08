from sqlalchemy import text
from redis import Redis

from app.core.config import settings
from app.core.database import engine

redis_client = Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)


def check_postgres() -> bool:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return True


def check_redis() -> bool:
    return redis_client.ping()
