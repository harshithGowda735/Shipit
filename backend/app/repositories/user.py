from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User, UserRole


def get_by_email(session: Session, email: str) -> User | None:
    return session.scalar(select(User).where(User.email == email))


def get_by_id(session: Session, user_id: UUID) -> User | None:
    return session.get(User, user_id)


def create(
    session: Session,
    *,
    full_name: str,
    email: str,
    password_hash: str,
    role: UserRole,
) -> User:
    user = User(
        full_name=full_name,
        email=email,
        password_hash=password_hash,
        role=role,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
