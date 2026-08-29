"""Pydantic request/response schemas for the greybox API."""

from __future__ import annotations

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# Health
# --------------------------------------------------------------------------- #


class HealthResponse(BaseModel):
    status: str = Field(description="'healthy' if all dependencies are up, else 'degraded'")
    qdrant: str
    redis: str


# --------------------------------------------------------------------------- #
# Ingestion
# --------------------------------------------------------------------------- #


class IngestResponse(BaseModel):
    documents_processed: int
    chunks_created: int
    collection: str


# --------------------------------------------------------------------------- #
# Query
# --------------------------------------------------------------------------- #


class QueryRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)


class RetrievedChunk(BaseModel):
    score: float
    source: str
    content: str
    document_id: str | None = None
    chunk_id: str | None = None


class LatencyBreakdown(BaseModel):
    embedding_latency_ms: float
    qdrant_latency_ms: float
    llm_latency_ms: float
    total_latency_ms: float


class QueryResponse(BaseModel):
    query: str
    answer: str | None
    message: str | None = None
    cache_hit: bool
    latency_ms: float
    latency: LatencyBreakdown
    results: list[RetrievedChunk]


# --------------------------------------------------------------------------- #
# Metrics
# --------------------------------------------------------------------------- #


class LatencyPercentiles(BaseModel):
    p50: float
    p95: float
    p99: float


class RecentRequest(BaseModel):
    total_latency_ms: float
    ts: float
    cache_hit: bool


class MetricsResponse(BaseModel):
    total_queries: int
    cache_hits: int
    cache_misses: int
    cache_hit_rate: float
    latency: LatencyPercentiles
    recent: list[RecentRequest]


# --------------------------------------------------------------------------- #
# Evaluation
# --------------------------------------------------------------------------- #


class EvaluationQuestionResult(BaseModel):
    question: str
    hit: bool
    retrieved_sources: list[str]
    relevant_sources: list[str]


class EvaluationResponse(BaseModel):
    total_questions: int
    hits: int
    hit_at_5: float
    results: list[EvaluationQuestionResult]


# --------------------------------------------------------------------------- #
# Drift
# --------------------------------------------------------------------------- #


class DriftResponse(BaseModel):
    drift_score: float
    threshold: float
    drift_detected: bool
    baseline: bool = Field(description="Whether a baseline centroid exists")


class DriftCheckResponse(BaseModel):
    drift_detected: bool
    drift_score: float
    action: str = Field(description="'reindex_triggered' | 'none'")


class DriftSimulateResponse(BaseModel):
    simulated: bool
    file: str
    chunks_added: int
