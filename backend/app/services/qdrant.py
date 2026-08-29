"""All Qdrant interaction lives here.

The rest of the application never imports ``qdrant_client`` directly; it calls
these functions. Connection problems are raised as :class:`QdrantUnavailable`
with an actionable message.
"""

from __future__ import annotations

import numpy as np
from qdrant_client import AsyncQdrantClient, models

from app.config import get_settings
from app.models.schemas import RetrievedChunk
from app.services import embeddings

_client: AsyncQdrantClient | None = None


class QdrantUnavailable(RuntimeError):
    """Raised when Qdrant cannot be reached or a call fails."""


def get_client() -> AsyncQdrantClient:
    global _client
    if _client is None:
        _client = AsyncQdrantClient(url=get_settings().qdrant_url, timeout=30.0)
    return _client


async def ping() -> bool:
    try:
        await get_client().get_collections()
        return True
    except Exception:  # noqa: BLE001 - health check must not raise
        return False


async def create_collection_if_not_exists() -> None:
    client = get_client()
    collection = get_settings().qdrant_collection
    try:
        exists = await client.collection_exists(collection)
        if exists:
            return
        await client.create_collection(
            collection_name=collection,
            vectors_config=models.VectorParams(
                size=embeddings.get_dimension(),
                distance=models.Distance.COSINE,
            ),
        )
    except Exception as exc:  # noqa: BLE001
        raise QdrantUnavailable(
            f"Could not create/verify collection '{collection}' at "
            f"{get_settings().qdrant_url}: {exc}"
        ) from exc


async def reset_collection() -> None:
    """Drop and recreate the collection so a full ingestion is authoritative
    (points from documents that no longer exist do not linger)."""
    client = get_client()
    collection = get_settings().qdrant_collection
    try:
        if await client.collection_exists(collection):
            await client.delete_collection(collection)
    except Exception as exc:  # noqa: BLE001
        raise QdrantUnavailable(f"Could not drop collection '{collection}': {exc}") from exc
    await create_collection_if_not_exists()


async def upsert_documents(points: list[models.PointStruct]) -> None:
    if not points:
        return
    try:
        await get_client().upsert(
            collection_name=get_settings().qdrant_collection,
            points=points,
            wait=True,
        )
    except Exception as exc:  # noqa: BLE001
        raise QdrantUnavailable(f"Upsert failed: {exc}") from exc


async def search(vector: list[float], top_k: int = 5) -> list[RetrievedChunk]:
    try:
        hits = await get_client().query_points(
            collection_name=get_settings().qdrant_collection,
            query=vector,
            limit=top_k,
            with_payload=True,
        )
    except Exception as exc:  # noqa: BLE001
        raise QdrantUnavailable(f"Search failed: {exc}") from exc

    results: list[RetrievedChunk] = []
    for point in hits.points:
        payload = point.payload or {}
        results.append(
            RetrievedChunk(
                score=float(point.score),
                source=payload.get("source", "unknown"),
                content=payload.get("content", ""),
                document_id=payload.get("document_id"),
                chunk_id=payload.get("chunk_id"),
            )
        )
    return results


async def iter_all_vectors(batch: int = 256) -> np.ndarray:
    """Return every stored vector as a (n, dim) array. Used for drift centroids."""
    client = get_client()
    collection = get_settings().qdrant_collection
    vectors: list[list[float]] = []
    offset = None
    try:
        while True:
            records, offset = await client.scroll(
                collection_name=collection,
                limit=batch,
                offset=offset,
                with_payload=False,
                with_vectors=True,
            )
            for rec in records:
                if rec.vector is not None:
                    vectors.append(rec.vector)  # type: ignore[arg-type]
            if offset is None:
                break
    except Exception as exc:  # noqa: BLE001
        raise QdrantUnavailable(f"Scroll failed: {exc}") from exc

    if not vectors:
        return np.zeros((0, embeddings.get_dimension()), dtype=np.float32)
    return np.asarray(vectors, dtype=np.float32)


async def delete_collection() -> None:
    try:
        await get_client().delete_collection(get_settings().qdrant_collection)
    except Exception as exc:  # noqa: BLE001
        raise QdrantUnavailable(f"Delete failed: {exc}") from exc


async def get_collection_stats() -> dict:
    client = get_client()
    collection = get_settings().qdrant_collection
    try:
        if not await client.collection_exists(collection):
            return {"exists": False, "points_count": 0, "collection": collection}
        info = await client.get_collection(collection)
        return {
            "exists": True,
            "collection": collection,
            "points_count": info.points_count or 0,
            "status": str(info.status),
            "vector_size": info.config.params.vectors.size,  # type: ignore[union-attr]
        }
    except Exception as exc:  # noqa: BLE001
        raise QdrantUnavailable(f"Stats failed: {exc}") from exc
