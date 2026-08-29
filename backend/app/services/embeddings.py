"""Local embedding service backed by sentence-transformers.

The model is loaded once per process and reused. Embeddings are L2-normalized
so that a dot product equals cosine similarity, matching the Qdrant collection's
cosine distance configuration.
"""

from __future__ import annotations

import threading

import numpy as np

from app.config import get_settings

_model = None
_lock = threading.Lock()


def _load_model():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                # Imported lazily so that importing this module (e.g. in tests
                # that monkeypatch the model) does not pull in torch eagerly.
                from sentence_transformers import SentenceTransformer

                _model = SentenceTransformer(get_settings().embedding_model)
    return _model


def warmup() -> None:
    """Force model load. Called on application startup."""
    _load_model()


def get_dimension() -> int:
    """Vector dimension reported by the loaded embedding model."""
    return int(_load_model().get_sentence_embedding_dimension())


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed a batch of texts. Returns a (len(texts), dim) float32 array."""
    if not texts:
        return np.zeros((0, get_dimension()), dtype=np.float32)
    model = _load_model()
    vectors = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return np.asarray(vectors, dtype=np.float32)


def embed_query(text: str) -> list[float]:
    """Embed a single query string into a plain list of floats."""
    return embed_texts([text])[0].tolist()
