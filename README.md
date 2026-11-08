# Shipit

Shipit is a proof-of-engineering assessment platform. The current backend is a
FastAPI service backed by PostgreSQL and Redis.

## Run the development stack

1. Copy `.env.example` to `.env` and replace the example database password.
   Keep the password in `POSTGRES_PASSWORD` and `DATABASE_URL` in sync.
2. Start the services from the repository root:

   ```sh
   docker compose up --build
   ```

3. Check `http://localhost:8000/health` for API liveness and
   `http://localhost:8000/health/dependencies` for PostgreSQL and Redis status.
   Dependency failures return HTTP 503 and are logged by the backend.

To stop the stack without deleting the database volume, run
`docker compose down`.

## Run backend tests

From `backend/`, run:

```sh
.venv/bin/python -m unittest discover -s tests -v
```
