from fastapi import APIRouter

from backend.config.settings import settings
from backend.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        application=settings.app_name,
        version=settings.app_version,
    )
