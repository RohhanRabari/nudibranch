"""Intelligent caching layer for marine data with multi-tier storage.

Provides caching with:
- Primary: aiocache with Redis backend (optional)
- Fallback: diskcache for offline operation
- Different TTLs per data type
"""

import functools
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable, Optional

import diskcache
from dotenv import load_dotenv

load_dotenv()


class DataCache:
    """Multi-tier cache with Redis primary and diskcache fallback.

    TTL configurations:
    - weather: 1800s (30 minutes) - changes frequently
    - marine: 1800s (30 minutes) - wave/swell conditions
    - tides: 43200s (12 hours) - predictable, slow changing
    - turbidity: 21600s (6 hours) - satellite data updated less frequently
    """

    DEFAULT_TTLS = {
        "weather": 1800,     # 30 minutes
        "marine": 1800,      # 30 minutes
        "tides": 43200,      # 12 hours
        "turbidity": 21600,  # 6 hours
    }

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        redis_url: Optional[str] = None,
        use_redis: bool = True,
    ) -> None:
        """Initialize the cache.

        Args:
            cache_dir: Directory for disk cache (default: .cache)
            redis_url: Redis connection URL (default: from REDIS_URL env var)
            use_redis: Whether to attempt Redis connection
        """
        # Setup disk cache (always available)
        if cache_dir is None:
            cache_dir = os.getenv("CACHE_DIR", ".cache")

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.disk_cache = diskcache.Cache(str(self.cache_dir))

        # Try Redis if enabled
        self.redis_cache: Optional[Any] = None
        self.redis_available = False

        if use_redis:
            redis_url = redis_url or os.getenv("REDIS_URL")
            if redis_url:
                try:
                    import aiocache
                    from aiocache.serializers import JsonSerializer

                    self.redis_cache = aiocache.Cache(
                        aiocache.Cache.REDIS,
                        endpoint=redis_url.split("://")[1].split(":")[0],
                        port=int(redis_url.split(":")[-1].split("/")[0]),
                        serializer=JsonSerializer(),
                    )
                    self.redis_available = True
                except (ImportError, Exception):
                    # Redis not available, fall back to disk cache only
                    self.redis_available = False

    def _make_key(self, data_type: str, lat: float, lng: float, **kwargs: Any) -> str:
        """Generate cache key from location and data type.

        Format: {data_type}:{lat:.3f}:{lng:.3f}:{hash}

        Args:
            data_type: Type of data (weather, marine, tides, turbidity)
            lat: Latitude (rounded to 3 decimal places)
            lng: Longitude (rounded to 3 decimal places)
            **kwargs: Additional parameters to include in key

        Returns:
            Cache key string
        """
        # Round coordinates to ~100m precision
        base_key = f"{data_type}:{lat:.3f}:{lng:.3f}"

        # Add hash of additional parameters if any
        if kwargs:
            param_str = json.dumps(kwargs, sort_keys=True)
            param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
            base_key = f"{base_key}:{param_hash}"

        return base_key

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Tries Redis first, falls back to disk cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        # Try Redis first if available
        if self.redis_available and self.redis_cache:
            try:
                value = await self.redis_cache.get(key)
                if value is not None:
                    return value
            except Exception:
                # Redis error, fall through to disk cache
                pass

        # Fall back to disk cache
        return self.disk_cache.get(key)

    async def set(self, key: str, value: Any, ttl: int) -> None:
        """Set value in cache with TTL.

        Stores in both Redis (if available) and disk cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        # Store in Redis if available
        if self.redis_available and self.redis_cache:
            try:
                await self.redis_cache.set(key, value, ttl=ttl)
            except Exception:
                # Redis error, continue with disk cache
                pass

        # Always store in disk cache
        self.disk_cache.set(key, value, expire=ttl)

    async def invalidate(self, key: str) -> None:
        """Remove key from cache.

        Args:
            key: Cache key to remove
        """
        # Remove from Redis if available
        if self.redis_available and self.redis_cache:
            try:
                await self.redis_cache.delete(key)
            except Exception:
                pass

        # Remove from disk cache
        self.disk_cache.delete(key)

    async def invalidate_location(self, lat: float, lng: float) -> None:
        """Clear all cached data for a location.

        Args:
            lat: Latitude
            lng: Longitude
        """
        # Pattern to match all data types for this location
        pattern = f"*:{lat:.3f}:{lng:.3f}*"

        # Clear from disk cache
        # diskcache doesn't support pattern matching, so we need to iterate
        keys_to_delete = []
        for key in self.disk_cache:
            if f":{lat:.3f}:{lng:.3f}" in str(key):
                keys_to_delete.append(key)

        for key in keys_to_delete:
            self.disk_cache.delete(key)

        # Clear from Redis if available
        if self.redis_available and self.redis_cache:
            try:
                # Note: This requires Redis SCAN command support
                # For simplicity, we'll just delete known data types
                for data_type in self.DEFAULT_TTLS.keys():
                    key = self._make_key(data_type, lat, lng)
                    await self.redis_cache.delete(key)
            except Exception:
                pass

    def close(self) -> None:
        """Close cache connections."""
        if self.disk_cache:
            self.disk_cache.close()


def cached_by_location(
    data_type: str,
    ttl: Optional[int] = None,
) -> Callable:
    """Decorator to cache function results by location.

    Args:
        data_type: Type of data (weather, marine, tides, turbidity)
        ttl: Time to live in seconds (uses default if None)

    Returns:
        Decorator function

    Example:
        >>> @cached_by_location("marine", ttl=1800)
        ... async def fetch_conditions(cache: DataCache, lat: float, lng: float):
        ...     # Expensive operation
        ...     return data
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(
            cache: DataCache, lat: float, lng: float, *args: Any, **kwargs: Any
        ) -> Any:
            # Determine TTL
            cache_ttl = ttl if ttl is not None else cache.DEFAULT_TTLS.get(data_type, 3600)

            # Generate cache key
            key = cache._make_key(data_type, lat, lng, **kwargs)

            # Try to get from cache
            cached_value = await cache.get(key)
            if cached_value is not None:
                return cached_value

            # Cache miss - call the function
            result = await func(cache, lat, lng, *args, **kwargs)

            # Store in cache
            await cache.set(key, result, cache_ttl)

            return result

        return wrapper

    return decorator
