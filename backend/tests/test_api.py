import pytest
from fastapi.testclient import TestClient

from app.models.schemas import RetrievedChunk
from tests.conftest import FakeSTModel


@pytest.fixture
def client(monkeypatch, fake_redis):
    from app import main
    from app.services import embeddings, qdrant, rag

    monkeypatch.setattr(embeddings, "_model", FakeSTModel())

    async def _noop():
        return None

    monkeypatch.setattr(qdrant, "create_collection_if_not_exists", _noop)
    monkeypatch.setattr(qdrant, "ping", lambda: _true())
    monkeypatch.setattr("app.api.routes.health.redis_cache.ping", lambda: _true())

    async def fake_search(vector, top_k):
        return [
            RetrievedChunk(score=0.88, source="redis.md",
                           content="Redis keys expire via EXPIRE/TTL.",
                           document_id="d1", chunk_id="d1:0"),
            RetrievedChunk(score=0.61, source="qdrant.md",
                           content="Qdrant stores points in collections."),
        ][:top_k]

    monkeypatch.setattr("app.api.routes.query.qdrant_service.search", fake_search)

    async def fake_generate(question, chunks):
        return None, "LLM unavailable"

    monkeypatch.setattr(rag, "generate_answer", fake_generate)
    monkeypatch.setattr("app.api.routes.query.rag.generate_answer", fake_generate)

    with TestClient(main.app) as c:
        yield c


async def _true():
    return True


def test_health_reports_dependency_status(client):
    body = client.get("/health").json()
    assert body["status"] == "healthy"
    assert body["qdrant"] == "healthy"
    assert body["redis"] == "healthy"


def test_query_returns_chunks_even_when_llm_unavailable(client):
    resp = client.post("/api/query", json={"query": "How does Redis expiration work?", "top_k": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] is None
    assert body["message"] == "LLM unavailable"
    assert body["cache_hit"] is False
    assert body["results"][0]["source"] == "redis.md"
    assert body["latency"]["total_latency_ms"] >= 0


def test_repeated_query_is_served_from_cache(client):
    payload = {"query": "cache me", "top_k": 3}
    first = client.post("/api/query", json=payload).json()
    second = client.post("/api/query", json=payload).json()
    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert second["results"][0]["source"] == first["results"][0]["source"]


def test_metrics_endpoint_shape(client):
    client.post("/api/query", json={"query": "metrics probe", "top_k": 2})
    body = client.get("/api/metrics").json()
    assert body["total_queries"] >= 1
    assert set(body["latency"]) == {"p50", "p95", "p99"}
    assert 0.0 <= body["cache_hit_rate"] <= 1.0
    assert isinstance(body["recent"], list)
