"""Import model modules here so Alembic can register their tables."""

from app.models.user import User, UserRole

__all__ = ["User", "UserRole"]