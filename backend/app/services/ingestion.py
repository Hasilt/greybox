"""Document ingestion pipeline: scan -> chunk -> embed -> upsert.

Chunking is word-based and deterministic. Point IDs are derived deterministically
from the chunk identity so re-running ingestion is idempotent (an unchanged chunk
overwrites itself with identical content).
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from qdrant_client import models

from app.config import get_settings
from app.models.schemas import IngestResponse
from app.services import drift, embeddings, qdrant

_NAMESPACE = uuid.UUID("6f9619ff-8b86-d011-b42d-00cf4fc964ff")
_SUPPORTED_SUFFIXES = {".txt", ".md"}


@dataclass
class Chunk:
    document_id: str
    source: str
    chunk_id: str
    content: str
    content_hash: str
    version: int = 1

    def point_id(self) -> str:
        return str(uuid.uuid5(_NAMESPACE, self.chunk_id))

    def payload(self) -> dict:
        return {
            "document_id": self.document_id,
            "source": self.source,
            "chunk_id": self.chunk_id,
            "content": self.content,
            "content_hash": self.content_hash,
            "version": self.version,
        }


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Split ``text`` into overlapping word windows.

    Deterministic. Returns ``[]`` for empty/whitespace-only input.
    """
    words = text.split()
    if not words:
        return []
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    step = chunk_size - chunk_overlap
    chunks: list[str] = []
    for start in range(0, len(words), step):
        window = words[start : start + chunk_size]
        if window:
            chunks.append(" ".join(window))
        if start + chunk_size >= len(words):
            break
    return chunks


def _document_id(relative_path: str) -> str:
    return hashlib.sha1(relative_path.encode("utf-8")).hexdigest()[:16]


def build_chunks_for_file(path: Path, root: Path) -> list[Chunk]:
    settings = get_settings()
    text = path.read_text(encoding="utf-8", errors="ignore")
    rel = str(path.relative_to(root))
    doc_id = _document_id(rel)
    out: list[Chunk] = []
    for i, body in enumerate(
        chunk_text(text, settings.chunk_size, settings.chunk_overlap)
    ):
        out.append(
            Chunk(
                document_id=doc_id,
                source=path.name,
                chunk_id=f"{doc_id}:{i}",
                content=body,
                content_hash=hashlib.sha256(body.encode("utf-8")).hexdigest(),
            )
        )
    return out


def scan_documents() -> list[Path]:
    root = Path(get_settings().documents_dir)
    if not root.exists():
        return []
    return sorted(
        p
        for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in _SUPPORTED_SUFFIXES
    )


async def run_ingestion(update_baseline: bool = True) -> IngestResponse:
    settings = get_settings()
    root = Path(settings.documents_dir)
    files = scan_documents()

    # Full re-ingestion: rebuild the collection from scratch so it always
    # reflects exactly the current document set on disk.
    await qdrant.reset_collection()

    all_chunks: list[Chunk] = []
    for path in files:
        all_chunks.extend(build_chunks_for_file(path, root))

    documents_processed = len({c.document_id for c in all_chunks})

    if all_chunks:
        vectors = embeddings.embed_texts([c.content for c in all_chunks])
        points = [
            models.PointStruct(
                id=chunk.point_id(),
                vector=vectors[idx].tolist(),
                payload=chunk.payload(),
            )
            for idx, chunk in enumerate(all_chunks)
        ]
        await qdrant.upsert_documents(points)

        if update_baseline:
            centroid = drift.centroid_from_vectors(np.asarray(vectors))
            drift.save_baseline(centroid)

    return IngestResponse(
        documents_processed=documents_processed,
        chunks_created=len(all_chunks),
        collection=settings.qdrant_collection,
    )
