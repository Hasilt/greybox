"""Liveness / dependency health."""

from fastapi import APIRouter

from app.models.schemas import HealthResponse
from app.services import qdrant, redis_cache

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    qdrant_ok = await qdrant.ping()
    redis_ok = await redis_cache.ping()
    return HealthResponse(
        status="healthy" if (qdrant_ok and redis_ok) else "degraded",
        qdrant="healthy" if qdrant_ok else "unavailable",
        redis="healthy" if redis_ok else "unavailable",
    )
