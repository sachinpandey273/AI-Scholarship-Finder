import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.routes import router
from .core.config import get_settings
from .db.session import engine

settings = get_settings()

@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.validate_runtime()
    yield

app = FastAPI(title="Scholarship Finder API", version="1.0.0", openapi_url="/api/v1/openapi.json", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True, allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-ID"])

@app.middleware("http")
async def request_id(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

@app.get("/healthz")
def healthz(): return {"status": "ok"}

@app.get("/readyz")
def readyz():
    """Readiness is false until required stateful dependencies respond."""
    try:
        from sqlalchemy import text
        from redis import Redis
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        Redis.from_url(settings.redis_url, socket_connect_timeout=1).ping()
    except Exception as exc:
        raise HTTPException(503, "Database or Redis is not ready") from exc
    return {"status": "ready"}

app.include_router(router, prefix="/api/v1", tags=["v1"])
