import os
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault(
    "SECRET_KEY",
    "unit-test-secret-key-that-is-at-least-32-bytes-long",
)

from sqlalchemy.orm import Session

from app.core.database import get_db


class DatabaseDependencyTests(unittest.TestCase):
    def test_session_is_closed_when_dependency_finishes(self) -> None:
        session = Mock(spec=Session)

        with patch("app.core.database.SessionLocal", return_value=session):
            dependency = get_db()
            self.assertIs(next(dependency), session)
            dependency.close()

        session.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
