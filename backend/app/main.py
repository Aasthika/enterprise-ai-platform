from fastapi import FastAPI

from backend.config.settings import settings
from backend.routers.health import router as health_router

app = FastAPI(
    title="Enterprise AI Intelligence Platform",
    version=settings.app_version,
    description="Production-style backend foundation for the Enterprise AI Intelligence & Observability Platform.",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(health_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "message": "Welcome to the Enterprise AI Intelligence Platform API",
    }
