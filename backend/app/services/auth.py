from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole
from app.repositories import user as user_repository
from app.schemas.auth import LoginRequest
from app.schemas.user import UserRegister


class DuplicateEmailError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


def _is_email_conflict(error: IntegrityError) -> bool:
    original_error = error.orig
    if getattr(original_error, "sqlstate", None) == "23505":
        diagnostic = getattr(original_error, "diag", None)
        return getattr(diagnostic, "constraint_name", None) == "ix_users_email"
    return "unique constraint failed: users.email" in str(original_error).lower()


def register_user(session: Session, request: UserRegister) -> User:
    if user_repository.get_by_email(session, str(request.email)) is not None:
        raise DuplicateEmailError

    try:
        return user_repository.create(
            session,
            full_name=request.full_name,
            email=str(request.email),
            password_hash=hash_password(request.password),
            role=UserRole.STUDENT,
        )
    except IntegrityError as error:
        session.rollback()
        if _is_email_conflict(error):
            raise DuplicateEmailError from error
        raise


def authenticate_user(session: Session, request: LoginRequest) -> User:
    user = user_repository.get_by_email(session, str(request.email))
    if (
        user is None
        or not user.is_active
        or not verify_password(request.password, user.password_hash)
    ):
        raise InvalidCredentialsError
    return user
