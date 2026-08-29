"""In-memory latency + query metrics.

Not persisted: counters and the recent-request ring buffer reset on restart.
Percentiles are computed by the nearest-rank method rather than by averaging.
"""

from __future__ import annotations

import time
from collections import deque
from threading import Lock

from app.config import get_settings

_lock = Lock()
_recent: deque[dict] = deque(maxlen=get_settings().metrics_window)
_total_queries = 0


def reset() -> None:
    global _total_queries
    with _lock:
        _recent.clear()
        _total_queries = 0


def record_query(
    *,
    total_latency_ms: float,
    embedding_latency_ms: float = 0.0,
    qdrant_latency_ms: float = 0.0,
    llm_latency_ms: float = 0.0,
    cache_hit: bool = False,
) -> None:
    global _total_queries
    with _lock:
        _total_queries += 1
        _recent.append(
            {
                "total_latency_ms": round(total_latency_ms, 2),
                "embedding_latency_ms": round(embedding_latency_ms, 2),
                "qdrant_latency_ms": round(qdrant_latency_ms, 2),
                "llm_latency_ms": round(llm_latency_ms, 2),
                "cache_hit": cache_hit,
                "ts": time.time(),
            }
        )


def _percentile(sorted_values: list[float], pct: float) -> float:
    """Nearest-rank percentile. ``pct`` in [0, 100]."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return round(sorted_values[0], 2)
    rank = max(1, min(len(sorted_values), round(pct / 100 * len(sorted_values))))
    return round(sorted_values[rank - 1], 2)


def snapshot(cache_hits: int, cache_misses: int) -> dict:
    with _lock:
        recent = list(_recent)
        total = _total_queries

    latencies = sorted(r["total_latency_ms"] for r in recent)
    denom = cache_hits + cache_misses
    return {
        "total_queries": total,
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "cache_hit_rate": round(cache_hits / denom, 4) if denom else 0.0,
        "latency": {
            "p50": _percentile(latencies, 50),
            "p95": _percentile(latencies, 95),
            "p99": _percentile(latencies, 99),
        },
        "recent": [
            {
                "total_latency_ms": r["total_latency_ms"],
                "ts": r["ts"],
                "cache_hit": r["cache_hit"],
            }
            for r in recent
        ],
    }
