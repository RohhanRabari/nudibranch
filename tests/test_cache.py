"""Tests for caching layer."""

import asyncio
from pathlib import Path

import pytest

from nudibranch.cache import DataCache, cached_by_location


@pytest.fixture
def cache_dir(tmp_path):
    """Temporary cache directory."""
    return str(tmp_path / "test_cache")


@pytest.fixture
def cache(cache_dir):
    """Cache instance with disk storage only (no Redis for tests)."""
    return DataCache(cache_dir=cache_dir, use_redis=False)


@pytest.mark.asyncio
async def test_set_and_get(cache):
    """Test basic cache set and get operations."""
    await cache.set("test_key", {"data": "value"}, ttl=60)
    result = await cache.get("test_key")
    assert result == {"data": "value"}


@pytest.mark.asyncio
async def test_get_nonexistent(cache):
    """Test getting non-existent key returns None."""
    result = await cache.get("nonexistent_key")
    assert result is None


@pytest.mark.asyncio
async def test_invalidate(cache):
    """Test cache invalidation."""
    await cache.set("test_key", "value", ttl=60)
    assert await cache.get("test_key") == "value"

    await cache.invalidate("test_key")
    assert await cache.get("test_key") is None


@pytest.mark.asyncio
async def test_make_key(cache):
    """Test cache key generation."""
    key1 = cache._make_key("marine", 7.601, 98.366)
    key2 = cache._make_key("marine", 7.601, 98.366)
    key3 = cache._make_key("marine", 7.602, 98.366)
    key4 = cache._make_key("weather", 7.601, 98.366)

    # Same location and type should produce same key
    assert key1 == key2

    # Different location should produce different key
    assert key1 != key3

    # Different data type should produce different key
    assert key1 != key4

    # Keys should have expected format
    assert "marine:7.601:98.366" in key1
    assert "weather:7.601:98.366" in key4


@pytest.mark.asyncio
async def test_make_key_with_params(cache):
    """Test cache key generation with additional parameters."""
    key1 = cache._make_key("marine", 7.601, 98.366, days=7)
    key2 = cache._make_key("marine", 7.601, 98.366, days=7)
    key3 = cache._make_key("marine", 7.601, 98.366, days=3)

    # Same params should produce same key
    assert key1 == key2

    # Different params should produce different key
    assert key1 != key3


@pytest.mark.asyncio
async def test_ttl_expiration(cache):
    """Test that cache entries expire after TTL."""
    # Set with very short TTL
    await cache.set("short_lived", "value", ttl=1)

    # Should be available immediately
    assert await cache.get("short_lived") == "value"

    # Wait for expiration
    await asyncio.sleep(1.5)

    # Should be gone
    assert await cache.get("short_lived") is None


@pytest.mark.asyncio
async def test_invalidate_location(cache):
    """Test clearing all data for a location."""
    lat, lng = 7.601, 98.366

    # Store multiple data types for same location
    await cache.set(cache._make_key("marine", lat, lng), "marine_data", ttl=60)
    await cache.set(cache._make_key("weather", lat, lng), "weather_data", ttl=60)
    await cache.set(cache._make_key("tides", lat, lng), "tide_data", ttl=60)

    # Store data for different location
    await cache.set(cache._make_key("marine", 7.7, 98.4), "other_marine", ttl=60)

    # Verify all are cached
    assert await cache.get(cache._make_key("marine", lat, lng)) == "marine_data"
    assert await cache.get(cache._make_key("weather", lat, lng)) == "weather_data"
    assert await cache.get(cache._make_key("tides", lat, lng)) == "tide_data"
    assert await cache.get(cache._make_key("marine", 7.7, 98.4)) == "other_marine"

    # Invalidate the location
    await cache.invalidate_location(lat, lng)

    # First location should be cleared
    assert await cache.get(cache._make_key("marine", lat, lng)) is None
    assert await cache.get(cache._make_key("weather", lat, lng)) is None
    assert await cache.get(cache._make_key("tides", lat, lng)) is None

    # Other location should remain
    assert await cache.get(cache._make_key("marine", 7.7, 98.4)) == "other_marine"


@pytest.mark.asyncio
async def test_cached_by_location_decorator(cache):
    """Test the caching decorator."""
    call_count = 0

    @cached_by_location("marine", ttl=60)
    async def expensive_operation(cache: DataCache, lat: float, lng: float) -> dict:
        nonlocal call_count
        call_count += 1
        return {"lat": lat, "lng": lng, "data": "expensive_result"}

    # First call should execute function
    result1 = await expensive_operation(cache, 7.6, 98.37)
    assert result1 == {"lat": 7.6, "lng": 98.37, "data": "expensive_result"}
    assert call_count == 1

    # Second call should use cache
    result2 = await expensive_operation(cache, 7.6, 98.37)
    assert result2 == result1
    assert call_count == 1  # Function not called again

    # Different location should execute function
    result3 = await expensive_operation(cache, 7.7, 98.4)
    assert result3 == {"lat": 7.7, "lng": 98.4, "data": "expensive_result"}
    assert call_count == 2


@pytest.mark.asyncio
async def test_default_ttls(cache):
    """Test that default TTLs are configured correctly."""
    assert cache.DEFAULT_TTLS["weather"] == 1800  # 30 min
    assert cache.DEFAULT_TTLS["marine"] == 1800   # 30 min
    assert cache.DEFAULT_TTLS["tides"] == 43200   # 12 hours
    assert cache.DEFAULT_TTLS["turbidity"] == 21600  # 6 hours


@pytest.mark.asyncio
async def test_cache_directory_creation(tmp_path):
    """Test that cache directory is created if it doesn't exist."""
    cache_dir = tmp_path / "new_cache_dir"
    assert not cache_dir.exists()

    cache = DataCache(cache_dir=str(cache_dir), use_redis=False)
    assert cache_dir.exists()

    cache.close()


def test_cache_close(cache_dir):
    """Test cache cleanup."""
    cache = DataCache(cache_dir=cache_dir, use_redis=False)
    cache.close()  # Should not raise any errors
