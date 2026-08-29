"""Exercises the real embedding model. Runs inside the backend image where
torch + sentence-transformers are installed."""

import numpy as np

from app.services import embeddings


def test_model_loads_and_reports_expected_dimension():
    embeddings.warmup()
    assert embeddings.get_dimension() == 384  # BAAI/bge-small-en-v1.5


def test_same_input_produces_deterministic_embedding():
    a = embeddings.embed_query("How does Redis expiration work?")
    b = embeddings.embed_query("How does Redis expiration work?")
    assert a == b


def test_embeddings_are_normalized():
    vec = np.array(embeddings.embed_query("vector search"))
    assert np.isclose(np.linalg.norm(vec), 1.0, atol=1e-3)


def test_batch_shape_matches_input():
    vecs = embeddings.embed_texts(["one", "two", "three"])
    assert vecs.shape == (3, 384)
