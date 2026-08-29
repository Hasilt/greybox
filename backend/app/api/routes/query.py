"""Query pipeline and metrics endpoints."""

from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    LatencyBreakdown,
    MetricsResponse,
    QueryRequest,
    QueryResponse,
    RetrievedChunk,
)
from app.services import rag, redis_cache
from app.services import qdrant as qdrant_service
from app.services.embeddings import embed_query
from app.utils import metrics

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest) -> QueryResponse:
    started = time.perf_counter()

    # 1. Cache lookup
    cached = await redis_cache.get_cached(req.query)
    if cached is not None:
        total_ms = (time.perf_counter() - started) * 1000
        metrics.record_query(total_latency_ms=total_ms, cache_hit=True)
        results = [RetrievedChunk(**r) for r in cached.get("results", [])]
        return QueryResponse(
            query=req.query,
            answer=cached.get("answer"),
            message=cached.get("message"),
            cache_hit=True,
            latency_ms=round(total_ms, 2),
            latency=LatencyBreakdown(
                embedding_latency_ms=0.0,
                qdrant_latency_ms=0.0,
                llm_latency_ms=0.0,
                total_latency_ms=round(total_ms, 2),
            ),
            results=results,
        )

    # 2. Embed
    t0 = time.perf_counter()
    vector = embed_query(req.query)
    embedding_ms = (time.perf_counter() - t0) * 1000

    # 3. Vector search
    t0 = time.perf_counter()
    try:
        results = await qdrant_service.search(vector, top_k=req.top_k)
    except qdrant_service.QdrantUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    qdrant_ms = (time.perf_counter() - t0) * 1000

    # 4. Answer generation (optional, never fatal)
    t0 = time.perf_counter()
    answer, message = await rag.generate_answer(req.query, results)
    llm_ms = (time.perf_counter() - t0) * 1000

    total_ms = (time.perf_counter() - started) * 1000

    payload = {
        "answer": answer,
        "message": message,
        "results": [r.model_dump() for r in results],
    }
    await redis_cache.set_cached(req.query, payload)

    metrics.record_query(
        total_latency_ms=total_ms,
        embedding_latency_ms=embedding_ms,
        qdrant_latency_ms=qdrant_ms,
        llm_latency_ms=llm_ms,
        cache_hit=False,
    )

    return QueryResponse(
        query=req.query,
        answer=answer,
        message=message,
        cache_hit=False,
        latency_ms=round(total_ms, 2),
        latency=LatencyBreakdown(
            embedding_latency_ms=round(embedding_ms, 2),
            qdrant_latency_ms=round(qdrant_ms, 2),
            llm_latency_ms=round(llm_ms, 2),
            total_latency_ms=round(total_ms, 2),
        ),
        results=results,
    )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    return MetricsResponse(
        **metrics.snapshot(redis_cache.cache_hits, redis_cache.cache_misses)
    )
