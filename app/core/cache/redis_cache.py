"""Redis cache wrapper replacing @st.cache_data for distributed caching."""
import os
import pickle
import hashlib
import redis
from functools import wraps

_client = None

def get_redis_client() -> redis.Redis:
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
            except redis.exceptions.ConnectionError:
                # Fallback to computing without cache if Redis is unavailable
                return func(*args, **kwargs)
        return wrapper
    return decorator
