"""greybox — RAG retrieval reliability & observability platform (MVP)."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import drift, evaluation, health, ingestion, query
from app.services import embeddings, qdrant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("greybox")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("loading embedding model ...")
    embeddings.warmup()
    logger.info("embedding model ready (dim=%d)", embeddings.get_dimension())
    try:
        await qdrant.create_collection_if_not_exists()
    except qdrant.QdrantUnavailable as exc:
        logger.warning("qdrant not ready at startup: %s", exc)
    yield


app = FastAPI(
    title="greybox",
    version="0.1.0",
    summary="RAG retrieval reliability & observability platform",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(ingestion.router)
app.include_router(query.router)
app.include_router(evaluation.router)
app.include_router(drift.router)


@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {"service": "greybox", "docs": "/docs"}
