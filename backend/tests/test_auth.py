import os
import unittest
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault(
    "SECRET_KEY",
    "unit-test-secret-key-that-is-at-least-32-bytes-long",
)

from fastapi import HTTPException
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import require_roles
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import JWT_ALGORITHM, decode_access_token
from app.main import app
from app.models import User, UserRole


class AuthenticationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine(
            "sqlite+pysqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.session_factory = sessionmaker(
            bind=cls.engine,
            autoflush=False,
            autocommit=False,
        )
        Base.metadata.create_all(cls.engine)

    @classmethod
    def tearDownClass(cls) -> None:
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()

    def setUp(self) -> None:
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

        def override_get_db():
            with self.session_factory() as session:
                yield session

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        app.dependency_overrides.clear()

    def register(self, email: str = "student@example.com"):
        return self.client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Test Student",
                "email": email,
                "password": "StrongPassword!123",
            },
        )

    def login(self, email: str = "student@example.com"):
        return self.client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": "StrongPassword!123",
            },
        )

    def test_successful_registration_returns_public_student_profile(self) -> None:
        response = self.register(" Student@Example.com ")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["email"], "student@example.com")
        self.assertEqual(response.json()["role"], "student")
        self.assertNotIn("password_hash", response.json())
        self.assertNotIn("password", response.json())
        with self.session_factory() as session:
            user = session.get(User, UUID(response.json()["id"]))
            self.assertTrue(user.password_hash.startswith("$argon2id$"))

    def test_duplicate_email_registration_is_rejected(self) -> None:
        self.assertEqual(self.register().status_code, 201)

        response = self.register("STUDENT@example.com")

        self.assertEqual(response.status_code, 409)

    def test_invalid_email_is_rejected(self) -> None:
        response = self.register("not-an-email")

        self.assertEqual(response.status_code, 422)

    def test_registration_cannot_assign_a_privileged_role(self) -> None:
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Test Admin",
                "email": "admin@example.com",
                "password": "StrongPassword!123",
                "role": "platform_admin",
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_successful_login_returns_access_token(self) -> None:
        self.register()

        response = self.login("STUDENT@example.com")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["token_type"], "bearer")
        self.assertTrue(response.json()["access_token"])

    def test_incorrect_password_is_rejected(self) -> None:
        self.register()
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "student@example.com",
                "password": "IncorrectPassword!123",
            },
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Incorrect email or password")

    def test_jwt_signature_and_claims_validate(self) -> None:
        self.register()
        token = self.login().json()["access_token"]

        decoded_id = decode_access_token(token)

        self.assertIsNotNone(decoded_id)
        claims = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[JWT_ALGORITHM],
        )
        self.assertEqual(claims["sub"], str(decoded_id))

    def test_expired_token_is_rejected(self) -> None:
        expired_token = jwt.encode(
            {
                "sub": str(uuid4()),
                "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            },
            settings.SECRET_KEY.get_secret_value(),
            algorithm=JWT_ALGORITHM,
        )

        response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        self.assertEqual(response.status_code, 401)

    def test_token_without_expiration_is_rejected(self) -> None:
        token = jwt.encode(
            {"sub": str(uuid4())},
            settings.SECRET_KEY.get_secret_value(),
            algorithm=JWT_ALGORITHM,
        )

        response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(response.status_code, 401)

    def test_invalid_signature_is_rejected(self) -> None:
        token = jwt.encode(
            {
                "sub": str(uuid4()),
                "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
            },
            "a-different-key-that-is-at-least-32-bytes-long",
            algorithm=JWT_ALGORITHM,
        )

        response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(response.status_code, 401)

    def test_unauthorized_access_to_current_user_is_rejected(self) -> None:
        response = self.client.get("/api/v1/auth/me")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers["www-authenticate"], "Bearer")

    def test_role_based_access_rejects_student(self) -> None:
        registered_user = self.register().json()
        with self.session_factory() as session:
            student = session.get(User, UUID(registered_user["id"]))

        role_dependency = require_roles(UserRole.PLATFORM_ADMIN)
        with self.assertRaises(HTTPException) as raised:
            role_dependency(current_user=student)

        self.assertEqual(raised.exception.status_code, 403)

    def test_current_user_endpoint_returns_authenticated_profile(self) -> None:
        self.register()
        token = self.login().json()["access_token"]

        response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "student@example.com")
        self.assertNotIn("password_hash", response.json())


if __name__ == "__main__":
    unittest.main()
