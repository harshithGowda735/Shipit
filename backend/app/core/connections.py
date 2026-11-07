import os

from sqlalchemy import create_engine, text
from redis import Redis


DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

redis_client = Redis.from_url(
    REDIS_URL,
    decode_responses=True
)


def check_postgres():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True


def check_redis():
    return redis_client.ping()