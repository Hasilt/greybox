"""Retrieval evaluation endpoint."""

from fastapi import APIRouter, HTTPException

from app.models.schemas import EvaluationResponse
from app.services import evaluation
from app.services.qdrant import QdrantUnavailable

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


@router.post("/run", response_model=EvaluationResponse)
async def run() -> EvaluationResponse:
    try:
        return await evaluation.run_evaluation()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except QdrantUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
