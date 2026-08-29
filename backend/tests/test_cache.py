import pytest

from app.services import redis_cache


def test_query_normalization_collapses_whitespace_and_case():
    assert redis_cache.normalize_query("  How   DOES it Work?  ") == "how does it work?"
    assert redis_cache.make_key(" Hello World ") == redis_cache.make_key("hello world")


@pytest.mark.asyncio
async def test_cache_miss_then_hit(fake_redis):
    assert await redis_cache.get_cached("what is qdrant") is None
    assert redis_cache.cache_misses == 1
    assert redis_cache.cache_hits == 0

    await redis_cache.set_cached("what is qdrant", {"answer": "a vector db", "results": []})

    hit = await redis_cache.get_cached("  What is Qdrant  ")
    assert hit is not None
    assert hit["answer"] == "a vector db"
    assert redis_cache.cache_hits == 1
    assert redis_cache.cache_misses == 1


@pytest.mark.asyncio
async def test_set_cached_applies_ttl(fake_redis):
    await redis_cache.set_cached("ttl probe", {"answer": None, "results": []})
    ttl = await fake_redis.ttl(redis_cache.make_key("ttl probe"))
    assert 0 < ttl <= redis_cache.get_settings().cache_ttl_seconds
