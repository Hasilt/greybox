"""Document ingestion endpoint."""

from fastapi import APIRouter, HTTPException

from app.models.schemas import IngestResponse
from app.services import ingestion
from app.services.qdrant import QdrantUnavailable

router = APIRouter(prefix="/api", tags=["ingestion"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest() -> IngestResponse:
    try:
        return await ingestion.run_ingestion(update_baseline=True)
    except QdrantUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
