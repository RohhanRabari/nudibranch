#!/usr/bin/env python3
"""Example demonstrating the caching layer.

Shows how caching reduces API calls and improves performance.
Run with: python examples/test_cache.py
"""

import asyncio
import time

from nudibranch.cache import DataCache, cached_by_location
from nudibranch.clients.open_meteo import OpenMeteoClient


# Example cached function
@cached_by_location("marine", ttl=60)
async def fetch_marine_cached(
    cache: DataCache, lat: float, lng: float
) -> dict:
    """Fetch marine data with caching."""
    async with OpenMeteoClient() as client:
        return await client.fetch_marine(lat, lng)


async def main() -> None:
    """Demonstrate caching functionality."""
    print("Cache Performance Demonstration")
    print("=" * 60)

    # Initialize cache
    cache = DataCache(cache_dir=".cache_demo", use_redis=False)
    print(f"✓ Cache initialized (disk-based)")
    print(f"  Cache directory: {cache.cache_dir}")
    print(f"  Redis available: {cache.redis_available}")
    print()

    # Test location
    lat, lng = 7.601, 98.366  # Racha Yai

    # First fetch - will hit the API
    print(f"Fetching marine data for ({lat}, {lng})...")
    start = time.time()
    result1 = await fetch_marine_cached(cache, lat, lng)
    elapsed1 = time.time() - start
    print(f"✓ First fetch completed in {elapsed1:.3f}s (API call)")
    print(f"  Wave height: {result1['wave_height_m']:.2f}m")
    print()

    # Second fetch - will use cache
    print(f"Fetching same location again...")
    start = time.time()
    result2 = await fetch_marine_cached(cache, lat, lng)
    elapsed2 = time.time() - start
    print(f"✓ Second fetch completed in {elapsed2:.3f}s (CACHED)")
    print(f"  Wave height: {result2['wave_height_m']:.2f}m")
    print(f"  Speed improvement: {elapsed1/elapsed2:.1f}x faster")
    print()

    # Verify it's the same data
    assert result1 == result2
    print("✓ Cache integrity verified - data matches exactly")
    print()

    # Test cache key generation
    print("Cache Key Examples:")
    marine_key = cache._make_key("marine", lat, lng)
    weather_key = cache._make_key("weather", lat, lng)
    print(f"  Marine: {marine_key}")
    print(f"  Weather: {weather_key}")
    print()

    # Test manual cache operations
    print("Manual Cache Operations:")
    test_key = "test:manual"
    test_data = {"custom": "data", "value": 123}

    await cache.set(test_key, test_data, ttl=60)
    print(f"✓ Stored: {test_key} = {test_data}")

    retrieved = await cache.get(test_key)
    print(f"✓ Retrieved: {retrieved}")

    await cache.invalidate(test_key)
    print(f"✓ Invalidated: {test_key}")

    retrieved_after = await cache.get(test_key)
    print(f"  After invalidation: {retrieved_after}")
    print()

    # Test location invalidation
    print("Testing Location Invalidation:")
    # Cache multiple data types
    await cache.set(cache._make_key("marine", lat, lng), "marine_data", ttl=60)
    await cache.set(cache._make_key("weather", lat, lng), "weather_data", ttl=60)
    print(f"✓ Cached marine and weather data for ({lat}, {lng})")

    await cache.invalidate_location(lat, lng)
    print(f"✓ Invalidated all data for location ({lat}, {lng})")

    marine_check = await cache.get(cache._make_key("marine", lat, lng))
    weather_check = await cache.get(cache._make_key("weather", lat, lng))
    print(f"  Marine data after invalidation: {marine_check}")
    print(f"  Weather data after invalidation: {weather_check}")
    print()

    # Show configured TTLs
    print("Configured TTLs:")
    for data_type, ttl in cache.DEFAULT_TTLS.items():
        minutes = ttl / 60
        hours = ttl / 3600
        if hours >= 1:
            print(f"  {data_type:10s}: {hours:.1f} hours ({ttl}s)")
        else:
            print(f"  {data_type:10s}: {minutes:.0f} minutes ({ttl}s)")

    print()
    print("=" * 60)
    print("Cache demonstration complete!")
    print(f"Cache location: {cache.cache_dir}")

    # Cleanup
    cache.close()


if __name__ == "__main__":
    asyncio.run(main())
