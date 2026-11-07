
from fastapi import FastAPI, HTTPException
from app.core.connections import check_postgres, check_redis

app = FastAPI(
    title="Shipit API",
    description="Proof of Engineering Assessment Platform",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "message": "Welcome to Shipit",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "shipit-backend"
    }

@app.get("/health/dependencies")
def dependency_health():

    results = {}

    try:
        check_postgres()
        results["postgres"] = "connected"
    except Exception:
        results["postgres"] = "disconnected"

    try:
        check_redis()
        results["redis"] = "connected"
    except Exception:
        results["redis"] = "disconnected"

    if "disconnected" in results.values():
        raise HTTPException(
            status_code=503,
            detail=results
        )

    return {
        "status": "healthy",
        "dependencies": results
    }