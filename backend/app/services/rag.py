"""Answer generation.

The LLM is optional. Every failure path returns ``(None, reason)`` so the query
endpoint can still respond with retrieved chunks and scores.
"""

from __future__ import annotations

import logging

import httpx

from app.config import get_settings
from app.models.schemas import RetrievedChunk

logger = logging.getLogger("greybox.rag")

_PROMPT = (
    "You are a precise technical assistant. Answer the question using ONLY the "
    "context below. If the context does not contain the answer, say so.\n\n"
    "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
)


def _build_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    context = "\n\n---\n\n".join(
        f"[{c.source}] {c.content}" for c in chunks
    ) or "(no context retrieved)"
    return _PROMPT.format(context=context, question=question)


async def generate_answer(
    question: str, chunks: list[RetrievedChunk]
) -> tuple[str | None, str | None]:
    """Return ``(answer, error_message)``. Exactly one is non-None."""
    settings = get_settings()
    provider = settings.llm_provider.lower()
    prompt = _build_prompt(question, chunks)

    try:
        if provider == "ollama":
            return await _ollama(prompt, settings), None
        if provider == "openai":
            if not settings.openai_api_key:
                return None, "LLM unavailable (OPENAI_API_KEY not set)"
            return await _openai(prompt, settings), None
        return None, "LLM disabled (GREYBOX_LLM_PROVIDER=none)"
    except httpx.HTTPError as exc:
        logger.warning("LLM request failed: %s", exc)
        return None, "LLM unavailable"
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM generation error: %s", exc)
        return None, "LLM unavailable"


async def _ollama(prompt: str, settings) -> str:
    async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
        resp = await client.post(
            f"{settings.ollama_url.rstrip('/')}/api/generate",
            json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()


async def _openai(prompt: str, settings) -> str:
    async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.openai_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
