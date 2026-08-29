"""Embedding-drift detection via centroid cosine distance.

Approach (MVP): reduce the whole indexed corpus to its mean (L2-normalized)
embedding vector. Compare the current centroid against a saved baseline centroid
using cosine similarity; ``drift_score = 1 - cosine_similarity``.

The threshold (``GREYBOX_DRIFT_THRESHOLD``) is an operational knob, not a
statistically derived value.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from app.config import get_settings
from app.services import qdrant

logger = logging.getLogger("greybox.drift")


def centroid_from_vectors(vectors: np.ndarray) -> np.ndarray:
    """Mean vector, L2-normalized. Empty input -> zero vector."""
    if vectors.size == 0:
        return np.zeros(vectors.shape[1] if vectors.ndim == 2 else 0, dtype=np.float32)
    mean = np.asarray(vectors, dtype=np.float32).mean(axis=0)
    norm = float(np.linalg.norm(mean))
    if norm == 0.0:
        return mean
    return mean / norm


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def drift_score(baseline: np.ndarray, current: np.ndarray) -> float:
    return round(1.0 - cosine_similarity(baseline, current), 6)


def _baseline_file() -> Path:
    return Path(get_settings().baseline_centroid_path)


def save_baseline(centroid: np.ndarray) -> None:
    path = _baseline_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, np.asarray(centroid, dtype=np.float32))
    logger.info("saved baseline centroid -> %s", path)


def load_baseline() -> np.ndarray | None:
    path = _baseline_file()
    if not path.exists():
        return None
    return np.load(path)


async def current_centroid() -> np.ndarray:
    vectors = await qdrant.iter_all_vectors()
    return centroid_from_vectors(vectors)


async def compute_drift() -> dict:
    settings = get_settings()
    baseline = load_baseline()
    current = await current_centroid()

    if baseline is None:
        return {
            "drift_score": 0.0,
            "threshold": settings.drift_threshold,
            "drift_detected": False,
            "baseline": False,
        }

    score = drift_score(baseline, current)
    return {
        "drift_score": score,
        "threshold": settings.drift_threshold,
        "drift_detected": score > settings.drift_threshold,
        "baseline": True,
    }
