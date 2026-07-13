"""Redis cache wrapper replacing @st.cache_data for distributed caching."""

import hashlib
import os
import pickle
from functools import wraps

try:
    import redis
    _redis_available = True
except Exception:  # pragma: no cover - fallback when package not installed
    redis = None
    _redis_available = False

_client = None

def get_redis_client():
    """Return a Redis client or raise if redis package is unavailable."""
    if not _redis_available:
        raise RuntimeError("redis package is not installed; install with 'pip install redis'")
    global _client
    if _client is None:
        _client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
            decode_responses=False,
        )
    return _client


def redis_cache(ttl: int = 300, prefix: str = "bootcamp"):
    """Decorator: cache function result in Redis with given TTL (seconds)."""

    def decorator(func):
        if not _redis_available:
            @wraps(func)
            def passthrough(*args, **kwargs):
                return func(*args, **kwargs)
            return passthrough

        @wraps(func)
        def wrapper(*args, **kwargs):
            key_data = f"{prefix}:{func.__name__}:{args}:{sorted(kwargs.items())}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            try:
                client = get_redis_client()
                cached = client.get(cache_key)
                if cached:
                    return pickle.loads(cached)
                result = func(*args, **kwargs)
                client.setex(cache_key, ttl, pickle.dumps(result))
                return result
            except Exception:
                # Fallback to computing without cache if Redis is unavailable
                return func(*args, **kwargs)

        return wrapper

    return decorator
