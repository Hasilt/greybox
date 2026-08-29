"""Shared fixtures. External dependencies (embedding model, Qdrant, Redis) are
faked so the suite runs without network or GPU."""

from __future__ import annotations

import hashlib

import numpy as np
import pytest

DIM = 8


class FakeSTModel:
    """Stand-in for sentence_transformers.SentenceTransformer."""

    def get_sentence_embedding_dimension(self) -> int:
        return DIM

    def encode(self, texts, normalize_embeddings=True, convert_to_numpy=True,
               show_progress_bar=False):
        out = np.stack([_deterministic_vec(t) for t in texts])
        if normalize_embeddings:
            norms = np.linalg.norm(out, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            out = out / norms
        return out.astype(np.float32)


def _deterministic_vec(text: str) -> np.ndarray:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    raw = np.frombuffer(digest[:DIM], dtype=np.uint8).astype(np.float32)
    return raw - raw.mean()


@pytest.fixture
def fake_embeddings(monkeypatch):
    from app.services import embeddings

    monkeypatch.setattr(embeddings, "_model", FakeSTModel())
    return embeddings


@pytest.fixture
def fake_redis(monkeypatch):
    import fakeredis.aioredis

    from app.services import redis_cache

    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    redis_cache.set_client(client)
    redis_cache.reset_counters()
    yield client
    redis_cache.set_client(None)  # type: ignore[arg-type]
    redis_cache.reset_counters()
