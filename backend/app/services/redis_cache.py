"""Redis caching service with monitoring and proper invalidation."""

import redis
import json
import logging
from typing import Optional, Any, Dict
from functools import wraps
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

# Cache metrics for monitoring
cache_metrics = {
    "hits": 0,
    "misses": 0,
    "invalidations": 0,
    "errors": 0,
    "last_reset": datetime.utcnow().isoformat()
}


class RedisCache:
    """Redis cache manager with monitoring and invalidation tracking."""

    def __init__(self):
        """Initialize Redis connection."""
        self.enabled = settings.REDIS_ENABLED
        self.client = None

        if self.enabled:
            try:
                self.client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                self.client.ping()
                logger.info(f"✓ Redis connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            except Exception as e:
                logger.error(f"❌ Redis connection failed: {e}")
                self.enabled = False
                self.client = None

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.enabled or not self.client:
            return None

        try:
            value = self.client.get(key)
            if value:
                cache_metrics["hits"] += 1
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            else:
                cache_metrics["misses"] += 1
                logger.debug(f"Cache MISS: {key}")
                return None
        except Exception as e:
            cache_metrics["errors"] += 1
            logger.error(f"Cache GET error for key '{key}': {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default: 5 minutes)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.client:
            return False

        try:
            serialized = json.dumps(value, default=str)
            self.client.setex(key, ttl, serialized)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            cache_metrics["errors"] += 1
            logger.error(f"Cache SET error for key '{key}': {e}")
            return False

    def invalidate(self, key: str) -> bool:
        """
        Invalidate (delete) a cache key.

        Args:
            key: Cache key to invalidate

        Returns:
            True if key was deleted, False otherwise
        """
        if not self.enabled or not self.client:
            return False

        try:
            deleted = self.client.delete(key)
            if deleted:
                cache_metrics["invalidations"] += 1
                logger.info(f"Cache INVALIDATED: {key}")
            return bool(deleted)
        except Exception as e:
            cache_metrics["errors"] += 1
            logger.error(f"Cache INVALIDATE error for key '{key}': {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.

        Args:
            pattern: Pattern to match (e.g., "games:*")

        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.client:
            return 0

        try:
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                cache_metrics["invalidations"] += deleted
                logger.info(f"Cache INVALIDATED PATTERN: {pattern} ({deleted} keys)")
                return deleted
            return 0
        except Exception as e:
            cache_metrics["errors"] += 1
            logger.error(f"Cache INVALIDATE PATTERN error for '{pattern}': {e}")
            return 0

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get cache performance metrics.

        Returns:
            Dictionary with hit rate, miss rate, and other metrics
        """
        total_requests = cache_metrics["hits"] + cache_metrics["misses"]
        hit_rate = (cache_metrics["hits"] / total_requests * 100) if total_requests > 0 else 0
        miss_rate = (cache_metrics["misses"] / total_requests * 100) if total_requests > 0 else 0

        return {
            "enabled": self.enabled,
            "connected": bool(self.client),
            "total_requests": total_requests,
            "hits": cache_metrics["hits"],
            "misses": cache_metrics["misses"],
            "hit_rate_percent": round(hit_rate, 2),
            "miss_rate_percent": round(miss_rate, 2),
            "invalidations": cache_metrics["invalidations"],
            "errors": cache_metrics["errors"],
            "last_reset": cache_metrics["last_reset"]
        }

    def reset_metrics(self):
        """Reset cache metrics."""
        cache_metrics["hits"] = 0
        cache_metrics["misses"] = 0
        cache_metrics["invalidations"] = 0
        cache_metrics["errors"] = 0
        cache_metrics["last_reset"] = datetime.utcnow().isoformat()
        logger.info("Cache metrics reset")

    def health_check(self) -> Dict[str, Any]:
        """
        Check Redis health.

        Returns:
            Health status dict
        """
        if not self.enabled:
            return {"status": "disabled", "message": "Redis caching is disabled"}

        if not self.client:
            return {"status": "unhealthy", "message": "Redis client not initialized"}

        try:
            self.client.ping()
            return {
                "status": "healthy",
                "host": settings.REDIS_HOST,
                "port": settings.REDIS_PORT,
                "db": settings.REDIS_DB
            }
        except Exception as e:
            return {"status": "unhealthy", "message": str(e)}


# Global cache instance
cache = RedisCache()


def cache_key(*args, **kwargs) -> str:
    """
    Generate a consistent cache key from arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Cache key string
    """
    parts = [str(arg) for arg in args]
    parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    return ":".join(parts)


def cached(key_prefix: str, ttl: int = 300, invalidate_on: Optional[list] = None):
    """
    Decorator for caching function results.

    Args:
        key_prefix: Prefix for cache key
        ttl: Time to live in seconds
        invalidate_on: List of operations that should invalidate this cache

    Usage:
        @cached("games:list", ttl=600)
        def get_games(limit: int = 20):
            return db.query(Game).limit(limit).all()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function args
            key = cache_key(key_prefix, *args, **kwargs)

            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                logger.debug(f"Returning cached result for {func.__name__}")
                return cached_value

            # Execute function
            logger.debug(f"Cache miss - executing {func.__name__}")
            result = func(*args, **kwargs)

            # Cache the result
            cache.set(key, result, ttl=ttl)

            return result

        # Store invalidation info for documentation
        wrapper._cache_info = {
            "key_prefix": key_prefix,
            "ttl": ttl,
            "invalidate_on": invalidate_on or []
        }

        return wrapper
    return decorator
