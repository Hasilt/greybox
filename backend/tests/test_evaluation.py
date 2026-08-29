import pytest

from app.models.schemas import RetrievedChunk
from app.services import evaluation


def test_score_question_hit_and_miss():
    assert evaluation.score_question(["redis.md", "qdrant.md"], ["redis.md"]) is True
    assert evaluation.score_question(["REDIS.MD"], ["redis.md"]) is True
    assert evaluation.score_question(["fastapi.md"], ["redis.md"]) is False
    assert evaluation.score_question([], ["redis.md"]) is False


@pytest.mark.asyncio
async def test_run_evaluation_computes_hit_at_5(monkeypatch, fake_embeddings):
    questions = [
        {"question": "redis ttl?", "relevant_sources": ["redis.md"]},
        {"question": "qdrant collections?", "relevant_sources": ["qdrant.md"]},
        {"question": "unanswerable?", "relevant_sources": ["missing.md"]},
    ]
    monkeypatch.setattr(evaluation, "load_questions", lambda: questions)

    async def fake_search(vector, top_k):
        return [RetrievedChunk(score=0.9, source="redis.md", content="x"),
                RetrievedChunk(score=0.8, source="qdrant.md", content="y")]

    monkeypatch.setattr(evaluation.qdrant, "search", fake_search)
    evaluation.EVAL_HISTORY.clear()

    result = await evaluation.run_evaluation()

    assert result.total_questions == 3
    assert result.hits == 2
    assert result.hit_at_5 == pytest.approx(2 / 3, abs=1e-4)
    assert len(result.results) == 3
    assert evaluation.EVAL_HISTORY[-1]["hits"] == 2
