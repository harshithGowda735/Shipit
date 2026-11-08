# Shipit

Shipit is a proof-of-engineering assessment platform. The current backend is a
FastAPI service backed by PostgreSQL and Redis.

## Run the development stack

1. Copy `.env.example` to `.env` and replace the example database password.
   Keep the password in `POSTGRES_PASSWORD` and `DATABASE_URL` in sync, and
   replace `SECRET_KEY` with a randomly generated value of at least 32 bytes.
2. Start the services from the repository root:

   ```sh
   docker compose up --build
   ```

3. Check `http://localhost:8000/health` for API liveness and
   `http://localhost:8000/health/dependencies` for PostgreSQL and Redis status.
   Dependency failures return HTTP 503 and are logged by the backend.

PostgreSQL and Redis ports are bound to localhost for development access only;
the backend reaches both services over the private Compose network.

## Database migrations

The backend uses Alembic for schema changes. From the repository root, apply
pending production migrations with:

```sh
docker compose exec backend alembic upgrade head
```

Migrations are deliberately not run automatically during API startup. Create
new revisions with
`docker compose exec backend alembic revision --autogenerate -m "describe the schema change"`.
Review generated revisions before applying them; model classes must be imported
from `app.models` so they are registered in `Base.metadata`.
The reversible smoke-test migration is isolated under `backend/tests/migrations`
and uses its own Alembic version table; it is not part of application upgrades.

## Authentication API

- `POST /api/v1/auth/register` creates a student account.
- `POST /api/v1/auth/login` returns a short-lived bearer access token.
- `GET /api/v1/auth/me` returns the authenticated user's public profile.

Send the token in an `Authorization: Bearer <access_token>` header. Registration
does not accept a role; elevated roles must be assigned through trusted
administrative workflows. Passwords are stored as Argon2 hashes and never
returned by the API.

To stop the stack without deleting the database volume, run
`docker compose down`.

## Run backend tests

From `backend/`, run:

```sh
.venv/bin/python -m unittest discover -s tests -v
```
