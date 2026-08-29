"""Drift inspection, simulation, and the synchronous auto-reindex trigger."""

from __future__ import annotations

import time
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.models.schemas import DriftCheckResponse, DriftResponse, DriftSimulateResponse
from app.services import drift, ingestion
from app.services.qdrant import QdrantUnavailable

router = APIRouter(prefix="/api/drift", tags=["drift"])

# Deliberately off-topic paragraphs (nothing to do with RAG / vector search /
# infrastructure) used to shift the corpus embedding distribution.
_OFF_TOPIC_PARAGRAPHS = [
    "Transhumant beekeepers move hives between valley pastures and high alpine "
    "meadows as the wildflower bloom climbs the slope through summer. Colonies "
    "foraging on rhododendron and clover produce a pale, slow-crystallizing honey "
    "that mountain cooperatives grade by aroma, water content, and pollen count.",
    "Inside natural limestone cheese caves the air holds a steady eleven degrees "
    "and near-saturated humidity. Wheels are turned, brushed, and rubbed with "
    "brine for months while a rind of moulds and coryneform bacteria matures, and "
    "the affineur reads the pitch of the paste by tapping each wheel with a mallet.",
    "Graziers rotate cattle across fenced paddocks so the forage recovers between "
    "bites. Rest periods of thirty to forty days let ryegrass and fescue rebuild "
    "root reserves, which lifts dry-matter yield and keeps the sward dense enough "
    "to shade out creeping thistle and dock.",
    "Timber barn frames are cut from spruce felled in winter when the sap is low. "
    "Mortise-and-tenon joints are pegged with riven oak trunnels and the bents are "
    "raised by hand with pike poles; the steep roof pitch sheds the heavy wet snow "
    "common above a thousand metres of elevation.",
    "Tidal salt marshes trap fine sediment as the flood current slackens, building "
    "creek levees and back-marsh basins. Cordgrass colonises the low marsh while "
    "glasswort and sea lavender follow on the higher terraces, and the whole "
    "platform accretes upward roughly in step with sea-level rise.",
    "A hand-weaver dresses the loom by winding a warp of even tension, threading "
    "each end through a heddle and a slot in the reed. Treadling lifts a shed, the "
    "shuttle carries the weft, and the beater packs each pick against the fell of "
    "the cloth at a steady picks-per-inch.",
    "Competitive freedivers train the mammalian dive reflex with breath-hold "
    "tables and slow equalisation drills. On descent the spleen contracts and "
    "releases stored red cells, the heart rate falls, and blood shifts to the core "
    "to protect the lungs against the rising ambient pressure.",
    "Medieval falconers manned a new hawk by carrying it hooded on the fist for "
    "long hours until it fed calmly through the jesses. Weight was watched to the "
    "gram, because a hawk flown too high in condition would ignore the lure and a "
    "hawk flown too low lacked the power to climb.",
]


def _generate_off_topic_doc(blocks: int) -> str:
    parts = ["# Unrelated Field Notes (drift simulation)\n"]
    for i in range(blocks):
        para = _OFF_TOPIC_PARAGRAPHS[i % len(_OFF_TOPIC_PARAGRAPHS)]
        parts.append(f"## Note {i + 1}\n\n{para}\n")
    return "\n".join(parts)


@router.get("", response_model=DriftResponse)
async def get_drift() -> DriftResponse:
    try:
        return DriftResponse(**await drift.compute_drift())
    except QdrantUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/simulate", response_model=DriftSimulateResponse)
async def simulate_drift() -> DriftSimulateResponse:
    """Demo mechanism (not a production drift simulator): add an unrelated
    document and re-index it WITHOUT updating the baseline centroid, so a
    subsequent GET /api/drift shows a raised score."""
    settings = get_settings()
    docs_dir = Path(settings.documents_dir)
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Write a large block of off-topic content (several files) so the shift is
    # big enough to actually cross a sane threshold for the demo.
    stamp = int(time.time())
    written: list[str] = []
    for n in range(4):
        fname = f"_drift_sim_{stamp}_{n}.md"
        (docs_dir / fname).write_text(_generate_off_topic_doc(blocks=80), encoding="utf-8")
        written.append(fname)

    try:
        before = await ingestion.qdrant.get_collection_stats()
        await ingestion.run_ingestion(update_baseline=False)
        after = await ingestion.qdrant.get_collection_stats()
    except QdrantUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    added = max(0, after.get("points_count", 0) - before.get("points_count", 0))
    return DriftSimulateResponse(
        simulated=True, file=", ".join(written), chunks_added=added
    )


@router.post("/check", response_model=DriftCheckResponse)
async def check_drift() -> DriftCheckResponse:
    """check drift -> if over threshold, re-index synchronously and recompute
    the baseline centroid."""
    try:
        state = await drift.compute_drift()
        if state["drift_detected"]:
            await ingestion.run_ingestion(update_baseline=True)
            return DriftCheckResponse(
                drift_detected=True,
                drift_score=state["drift_score"],
                action="reindex_triggered",
            )
        return DriftCheckResponse(
            drift_detected=False,
            drift_score=state["drift_score"],
            action="none",
        )
    except QdrantUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
