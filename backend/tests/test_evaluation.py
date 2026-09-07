import math

import pytest

from app.models.schemas import RetrievedChunk
from app.services import evaluation


def test_score_question_hit_and_miss():
    assert evaluation.score_question(["redis.md", "qdrant.md"], ["redis.md"]) is True
    assert evaluation.score_question(["REDIS.MD"], ["redis.md"]) is True
    assert evaluation.score_question(["fastapi.md"], ["redis.md"]) is False
    assert evaluation.score_question([], ["redis.md"]) is False


def test_reciprocal_rank():
    assert evaluation.reciprocal_rank(["redis.md"], ["redis.md"]) == pytest.approx(1.0)
    assert evaluation.reciprocal_rank(["a.md", "redis.md"], ["redis.md"]) == pytest.approx(0.5)
    assert evaluation.reciprocal_rank(["a.md", "b.md"], ["redis.md"]) == pytest.approx(0.0)
    assert evaluation.reciprocal_rank(["a.md"], []) == pytest.approx(0.0)
    assert evaluation.reciprocal_rank(["REDIS.MD"], ["redis.md"]) == pytest.approx(1.0)
    # first relevant source wins, later ones do not change the RR
    assert evaluation.reciprocal_rank(["a.md", "redis.md", "qdrant.md"], ["redis.md", "qdrant.md"]) == pytest.approx(0.5)


def test_recall_at_k():
    relevant = ["redis.md", "qdrant.md"]
    # both relevant sources retrieved within k
    assert evaluation.recall_at_k(["redis.md", "qdrant.md", "x.md"], relevant, 5) == pytest.approx(1.0)
    # only one of two retrieved
    assert evaluation.recall_at_k(["redis.md", "x.md"], relevant, 5) == pytest.approx(0.5)
    # none retrieved
    assert evaluation.recall_at_k(["x.md", "y.md"], relevant, 5) == pytest.approx(0.0)
    # k clips the window: relevant source outside top-k does not count
    assert evaluation.recall_at_k(["x.md", "y.md", "redis.md"], ["redis.md"], 2) == pytest.approx(0.0)
    # repeated sources count once
    assert evaluation.recall_at_k(["redis.md", "redis.md"], ["redis.md"], 5) == pytest.approx(1.0)
    # empty relevant sources -> 0.0, no division by zero
    assert evaluation.recall_at_k(["redis.md"], [], 5) == pytest.approx(0.0)


def test_ndcg_at_k():
    # relevant at rank 1: perfect ranking for a single relevant source
    assert evaluation.ndcg_at_k(["redis.md", "x.md"], ["redis.md"], 5) == pytest.approx(1.0)
    # relevant at rank 2: position discount applies
    expected = (1.0 / math.log2(3)) / (1.0 / math.log2(2))
    assert evaluation.ndcg_at_k(["x.md", "redis.md"], ["redis.md"], 5) == pytest.approx(expected)
    # no relevant source retrieved
    assert evaluation.ndcg_at_k(["x.md"], ["redis.md"], 5) == pytest.approx(0.0)
    # two relevant sources, perfect ranking
    relevant = ["redis.md", "qdrant.md"]
    assert evaluation.ndcg_at_k(["redis.md", "qdrant.md", "x.md"], relevant, 5) == pytest.approx(1.0)
    # two relevant sources, second one at rank 3
    dcg = 1.0 / math.log2(2) + 1.0 / math.log2(4)
    idcg = 1.0 / math.log2(2) + 1.0 / math.log2(3)
    assert evaluation.ndcg_at_k(["redis.md", "x.md", "qdrant.md"], relevant, 5) == pytest.approx(dcg / idcg)
    # repeated relevant sources only earn a gain once (deduplicated per source)
    assert evaluation.ndcg_at_k(["redis.md", "redis.md"], ["redis.md"], 5) == pytest.approx(1.0)
    # duplicate relevant chunks cannot push nDCG above 1
    assert evaluation.ndcg_at_k(["redis.md", "redis.md", "redis.md"], ["redis.md"], 5) <= 1.0
    # second occurrence of an already-seen relevant source gets no gain
    dcg_dup = 1.0 / math.log2(2) + 1.0 / math.log2(4)
    assert evaluation.ndcg_at_k(["redis.md", "x.md", "redis.md"], ["redis.md"], 5) == pytest.approx(dcg_dup)
    # two relevant sources but only one retrieved: capped by IDCG
    dcg = 1.0 / math.log2(3)
    assert evaluation.ndcg_at_k(["x.md", "redis.md"], relevant, 5) == pytest.approx(dcg / idcg)
    # empty relevant sources -> 0.0, no division by zero
    assert evaluation.ndcg_at_k(["redis.md"], [], 5) == pytest.approx(0.0)


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

    # per-question position-aware metrics
    assert result.results[0].rr == pytest.approx(1.0)  # redis.md at rank 1
    assert result.results[0].recall == pytest.approx(1.0)
    assert result.results[0].ndcg == pytest.approx(1.0)
    assert result.results[1].rr == pytest.approx(0.5)  # qdrant.md at rank 2
    assert result.results[1].recall == pytest.approx(1.0)
    assert result.results[1].ndcg == pytest.approx((1.0 / math.log2(3)) / (1.0 / math.log2(2)))
    assert result.results[2].rr == pytest.approx(0.0)
    assert result.results[2].recall == pytest.approx(0.0)
    assert result.results[2].ndcg == pytest.approx(0.0)

    # aggregate metrics
    assert result.mrr == pytest.approx(0.5, abs=1e-4)  # (1.0 + 0.5 + 0.0) / 3
    assert result.recall_at_5 == pytest.approx(2 / 3, abs=1e-4)  # (1.0 + 1.0 + 0.0) / 3
    assert result.ndcg_at_5 == pytest.approx((1.0 + (1.0 / math.log2(3)) / (1.0 / math.log2(2)) + 0.0) / 3, abs=1e-4)
    assert evaluation.EVAL_HISTORY[-1]["mrr"] == pytest.approx(0.5, abs=1e-4)
