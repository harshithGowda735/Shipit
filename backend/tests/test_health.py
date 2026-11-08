import os
import unittest
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault(
    "SECRET_KEY",
    "unit-test-secret-key-that-is-at-least-32-bytes-long",
)

from fastapi.testclient import TestClient

from app import main


class HealthEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(main.app)

    def tearDown(self) -> None:
        self.client.close()

    def test_root_returns_welcome_message(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "running")

    def test_health_returns_liveness(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    @patch("app.main.check_postgres", return_value=True)
    @patch("app.main.check_redis", return_value=True)
    def test_dependency_health_returns_healthy(
        self, _check_redis: object, _check_postgres: object
    ) -> None:
        response = self.client.get("/health/dependencies")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "healthy",
                "dependencies": {
                    "postgres": "connected",
                    "redis": "connected",
                },
            },
        )

    @patch("app.main.check_postgres", side_effect=RuntimeError("database down"))
    @patch("app.main.check_redis", return_value=True)
    def test_dependency_health_returns_503_on_failure(
        self, _check_redis: object, _check_postgres: object
    ) -> None:
        response = self.client.get("/health/dependencies")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()["detail"],
            {"postgres": "disconnected", "redis": "connected"},
        )


if __name__ == "__main__":
    unittest.main()
