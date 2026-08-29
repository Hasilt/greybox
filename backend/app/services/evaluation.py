"""Retrieval evaluation: Hit@5 against a ground-truth question set.

No LLM is involved. A question counts as a hit if any of its known
``relevant_sources`` appears among the sources of the top-5 retrieved chunks.
"""

from __future__ import annotations

import json
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


async def run_evaluation() -> EvaluationResponse:
    questions = load_questions()
    results: list[EvaluationQuestionResult] = []
    hits = 0

    for item in questions:
        question = item["question"]
        relevant = item.get("relevant_sources", [])
        vector = embeddings.embed_query(question)
        chunks = await qdrant.search(vector, top_k=TOP_K)
        retrieved = [c.source for c in chunks]
        hit = score_question(retrieved, relevant)
        hits += int(hit)
        results.append(
            EvaluationQuestionResult(
                question=question,
                hit=hit,
                retrieved_sources=retrieved,
                relevant_sources=relevant,
            )
        )

    total = len(questions)
    hit_at_5 = round(hits / total, 4) if total else 0.0
    EVAL_HISTORY.append(
        {"ts": time.time(), "total_questions": total, "hits": hits, "hit_at_5": hit_at_5}
    )
    return EvaluationResponse(
        total_questions=total, hits=hits, hit_at_5=hit_at_5, results=results
    )
