import numpy as np
import pytest

from app.services import drift


def test_identical_centroids_produce_approximately_zero_drift():
    vecs = np.random.default_rng(0).normal(size=(20, 16)).astype(np.float32)
    c = drift.centroid_from_vectors(vecs)
    assert drift.drift_score(c, c) == pytest.approx(0.0, abs=1e-6)


def test_different_centroids_produce_positive_drift():
    rng = np.random.default_rng(1)
    a = drift.centroid_from_vectors(rng.normal(loc=1.0, size=(20, 16)).astype(np.float32))
    b = drift.centroid_from_vectors(rng.normal(loc=-1.0, size=(20, 16)).astype(np.float32))
    assert drift.drift_score(a, b) > 0.0


def test_opposite_vectors_give_drift_near_two():
    a = np.array([1.0, 0.0, 0.0])
    b = np.array([-1.0, 0.0, 0.0])
    assert drift.drift_score(a, b) == pytest.approx(2.0, abs=1e-6)


def test_centroid_is_unit_norm():
    vecs = np.random.default_rng(2).normal(size=(10, 12)).astype(np.float32)
    c = drift.centroid_from_vectors(vecs)
    assert np.isclose(np.linalg.norm(c), 1.0, atol=1e-5)


def test_save_and_load_baseline_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(
        drift.get_settings(), "baseline_centroid_path", str(tmp_path / "c.npy")
    )
    assert drift.load_baseline() is None
    vec = np.arange(8, dtype=np.float32)
    drift.save_baseline(vec)
    np.testing.assert_allclose(drift.load_baseline(), vec)
