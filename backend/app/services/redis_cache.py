"""Redis-backed query cache plus in-memory hit/miss counters.

A cache or connection failure is treated as a miss and logged; it never breaks
the query path.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time

import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger("greybox.cache")

_client: aioredis.Redis | None = None

# In-memory counters (acceptable for the MVP; not persisted).
cache_hits = 0
cache_misses = 0

_WS = re.compile(r"\s+")


def get_client() -> aioredis.Redis:
    global _client
    if _client is None:
        _client = aioredis.from_url(
            get_settings().redis_url, decode_responses=True
        )
    return _client


def set_client(client: aioredis.Redis) -> None:
    """Test hook: inject a fake Redis client."""
    global _client
    _client = client


def reset_counters() -> None:
    global cache_hits, cache_misses
    cache_hits = 0
    cache_misses = 0


def normalize_query(query: str) -> str:
    return _WS.sub(" ", query.strip().lower())


def make_key(query: str) -> str:
    digest = hashlib.sha256(normalize_query(query).encode("utf-8")).hexdigest()
    return f"greybox:query:{digest}"


async def ping() -> bool:
    try:
        return bool(await get_client().ping())
    except Exception:  # noqa: BLE001
        return False


async def get_cached(query: str) -> dict | None:
    global cache_hits, cache_misses
    try:
        raw = await get_client().get(make_key(query))
    except Exception as exc:  # noqa: BLE001
        logger.warning("cache get failed, treating as miss: %s", exc)
        cache_misses += 1
        return None

    if raw is None:
        cache_misses += 1
        return None
    cache_hits += 1
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def set_cached(query: str, payload: dict) -> None:
    body = dict(payload)
    body["cached_at"] = time.time()
    try:
        await get_client().set(
            make_key(query),
            json.dumps(body),
            ex=get_settings().cache_ttl_seconds,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("cache set failed: %s", exc)
