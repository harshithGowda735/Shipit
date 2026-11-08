from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import InvalidTokenError, decode_access_token
from app.models.user import User, UserRole
from app.repositories import user as user_repository

bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    session: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None:
        raise _unauthorized()

    try:
        user_id: UUID = decode_access_token(credentials.credentials)
    except InvalidTokenError:
        raise _unauthorized() from None

    user = user_repository.get_by_id(session, user_id)
    if user is None or not user.is_active:
        raise _unauthorized()
    return user


def require_roles(*roles: UserRole) -> Callable[..., User]:
    allowed_roles = frozenset(roles)
    if not allowed_roles:
        raise ValueError("At least one role must be allowed")

    def check_role(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return check_role
