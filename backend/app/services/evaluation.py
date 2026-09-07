"""Retrieval evaluation: Hit@5, MRR, Recall@5 and nDCG@5 against a
ground-truth question set.

No LLM is involved. A question counts as a hit if any of its known
``relevant_sources`` appears among the sources of the top-5 retrieved chunks.
Relevance is binary and source-level: a retrieved chunk is relevant when its
``source`` is in the question's ``relevant_sources``. MRR rewards early
first-hits, Recall@5 measures coverage of the relevant sources, and nDCG@5
rewards ranking quality — all three see what Hit@5 alone cannot.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path

from app.config import get_settings
from app.models.schemas import EvaluationQuestionResult, EvaluationResponse
from app.services import embeddings, qdrant

TOP_K = 5

# Session-only history (list of aggregate dicts). Not persisted.
EVAL_HISTORY: list[dict] = []


def load_questions() -> list[dict]:
    path = Path(get_settings().evaluation_path)
    if not path.exists():
        raise FileNotFoundError(f"Evaluation set not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("questions.json must be a JSON array")
    return data


def score_question(retrieved_sources: list[str], relevant_sources: list[str]) -> bool:
    relevant = {s.lower() for s in relevant_sources}
    return any(src.lower() in relevant for src in retrieved_sources)


def reciprocal_rank(retrieved_sources: list[str], relevant_sources: list[str]) -> float:
    """1 / rank of the first relevant source in the ranking, else 0.0."""
    relevant = {s.lower() for s in relevant_sources}
    for rank, src in enumerate(retrieved_sources, start=1):
        if src.lower() in relevant:
            return 1.0 / rank
    return 0.0


def recall_at_k(retrieved_sources: list[str], relevant_sources: list[str], k: int) -> float:
    """Fraction of relevant sources that appear in the top-k (0.0 if no
    relevant sources are defined). Repeated sources count once."""
    if not relevant_sources:
        return 0.0
    relevant = {s.lower() for s in relevant_sources}
    found = {src.lower() for src in retrieved_sources[:k]} & relevant
    return len(found) / len(relevant)


def ndcg_at_k(retrieved_sources: list[str], relevant_sources: list[str], k: int) -> float:
    """Binary-relevance nDCG@k (0.0 if no relevant sources are defined).

    DCG sums ``1 / log2(rank + 1)`` over positions whose source is relevant.
    Because the ground truth is defined per *source* (document) and a source
    can span multiple chunks, only the **first occurrence** of each relevant
    source earns a gain — later chunks from the same source contribute 0, so
    DCG can never exceed IDCG. IDCG is the same sum over an ideal ranking of
    ``min(len(relevant), k)`` relevant results.
    """
    if not relevant_sources:
        return 0.0
    relevant = {s.lower() for s in relevant_sources}
    seen: set[str] = set()
    gains = []
    for src in retrieved_sources[:k]:
        key = src.lower()
        gains.append(1.0 if key in relevant and key not in seen else 0.0)
        if key in relevant:
            seen.add(key)
    dcg = sum(gain / math.log2(i + 1) for i, gain in enumerate(gains, start=1))
    ideal_len = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_len + 1))
    return dcg / idcg if idcg else 0.0


async def run_evaluation() -> EvaluationResponse:
    questions = load_questions()
    results: list[EvaluationQuestionResult] = []
    hits = 0
    rr_total = 0.0
    recall_total = 0.0
    ndcg_total = 0.0

    for item in questions:
        question = item["question"]
        relevant = item.get("relevant_sources", [])
        vector = embeddings.embed_query(question)
        chunks = await qdrant.search(vector, top_k=TOP_K)
        retrieved = [c.source for c in chunks]
        hit = score_question(retrieved, relevant)
        rr = reciprocal_rank(retrieved, relevant)
        recall = recall_at_k(retrieved, relevant, TOP_K)
        ndcg = ndcg_at_k(retrieved, relevant, TOP_K)
        hits += int(hit)
        rr_total += rr
        recall_total += recall
        ndcg_total += ndcg
        results.append(
            EvaluationQuestionResult(
                question=question,
                hit=hit,
                retrieved_sources=retrieved,
                relevant_sources=relevant,
                rr=rr,
                recall=recall,
                ndcg=ndcg,
            )
        )

    total = len(questions)
    hit_at_5 = round(hits / total, 4) if total else 0.0
    mrr = round(rr_total / total, 4) if total else 0.0
    recall_at_5 = round(recall_total / total, 4) if total else 0.0
    ndcg_at_5 = round(ndcg_total / total, 4) if total else 0.0
    EVAL_HISTORY.append(
        {
            "ts": time.time(),
            "total_questions": total,
            "hits": hits,
            "hit_at_5": hit_at_5,
            "mrr": mrr,
            "recall_at_5": recall_at_5,
            "ndcg_at_5": ndcg_at_5,
        }
    )
    return EvaluationResponse(
        total_questions=total,
        hits=hits,
        hit_at_5=hit_at_5,
        mrr=mrr,
        recall_at_5=recall_at_5,
        ndcg_at_5=ndcg_at_5,
        results=results,
    )
