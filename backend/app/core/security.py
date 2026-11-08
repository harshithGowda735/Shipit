from datetime import datetime, timedelta, timezone
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from jose import JWTError, jwt

from app.core.config import settings

JWT_ALGORITHM = "HS256"
password_hasher = PasswordHasher()


class InvalidTokenError(Exception):
    pass


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except VerificationError:
        return False


def create_access_token(user_id: UUID) -> str:
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    claims = {
        "sub": str(user_id),
        "iat": issued_at,
        "exp": expires_at,
    }
    return jwt.encode(
        claims,
        settings.SECRET_KEY.get_secret_value(),
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> UUID:
    try:
        claims = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[JWT_ALGORITHM],
            options={"require_exp": True, "require_sub": True},
        )
        return UUID(claims["sub"])
    except (JWTError, KeyError, TypeError, ValueError) as error:
        raise InvalidTokenError from error
