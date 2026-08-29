from types import SimpleNamespace

import pytest

from app.services import qdrant


class _FakeClient:
    def __init__(self, points):
        self._points = points
        self.last_call = {}

    async def query_points(self, collection_name, query, limit, with_payload):
        self.last_call = {"collection": collection_name, "limit": limit}
        return SimpleNamespace(points=self._points[:limit])


@pytest.mark.asyncio
async def test_search_maps_payload_into_retrieved_chunks(monkeypatch):
    fake_points = [
        SimpleNamespace(
            score=0.91,
            payload={
                "source": "redis.md",
                "content": "Keys can be given a TTL with EXPIRE.",
                "document_id": "doc1",
                "chunk_id": "doc1:0",
            },
        ),
        SimpleNamespace(
            score=0.72,
            payload={"source": "qdrant.md", "content": "Collections hold points."},
        ),
    ]
    client = _FakeClient(fake_points)
    monkeypatch.setattr(qdrant, "get_client", lambda: client)

    results = await qdrant.search([0.0] * 8, top_k=5)

    assert [r.source for r in results] == ["redis.md", "qdrant.md"]
    assert results[0].score == pytest.approx(0.91)
    assert results[0].content.startswith("Keys can be given a TTL")
    assert results[0].chunk_id == "doc1:0"
    assert client.last_call["limit"] == 5


@pytest.mark.asyncio
async def test_search_failure_raises_qdrant_unavailable(monkeypatch):
    class _Boom:
        async def query_points(self, **_):
            raise ConnectionError("refused")

    monkeypatch.setattr(qdrant, "get_client", lambda: _Boom())
    with pytest.raises(qdrant.QdrantUnavailable):
        await qdrant.search([0.0] * 8, top_k=5)
