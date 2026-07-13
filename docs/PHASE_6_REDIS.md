# Phase 6: Redis Caching Layer

## Overview

In this phase, we replace Streamlit's built-in `@st.cache_data` memory cache with a **distributed Redis cache**.
This is crucial as our application scales because:
1. In production, Streamlit apps are often load-balanced across multiple instances. Local memory cache is useless across nodes.
2. In-memory caching takes up valuable application RAM. Redis moves memory pressure to a dedicated high-performance datastore.
3. Redis caches persist across container restarts and Streamlit app reruns.

**Time to Complete:** 1 hour
**Tech Stack:** Python, Redis, Docker

---

## What We Built

1. **Redis Docker Service:** Added to `docker-compose.yml` with a persistent volume to ensure cache durability across restarts.
2. **`redis_cache` Decorator:** Implemented in `app/core/cache/redis_cache.py`. It:
   - Hashes function arguments to create a unique cache key.
   - Checks Redis before executing the function.
   - Pickles and stores the result upon cache miss with a configured TTL (Time to Live).
3. **ETL Replacement:** Replaced Streamlit's `@st.cache_data` with `@redis_cache` in `app/core/etl/prices.py`.

---

## Core Concepts

### Distributed Caching
When running a data engineering stack or web app across multiple instances (e.g. Kubernetes, AWS ECS, or GCP Cloud Run), a local memory cache only benefits users hitting that specific container. Redis provides a centralized cache that all instances share.

### Serialization (Pickling)
Unlike simple strings, Python objects (like Pandas DataFrames) must be serialized into bytes before storing in Redis. We use Python's built-in `pickle` module for this. Note: Only unpickle data from trusted sources!

### TTL (Time To Live)
Financial data gets stale. We apply a 5-minute (300 seconds) TTL to our `load_prices_daily` function. Redis automatically deletes the key after 300 seconds, ensuring the next user request hits the yfinance API to fetch fresh data.

### Cache Key Strategy
A cache key must uniquely identify the function and its parameters. We use `hashlib.md5` on the function name, arguments, and keyword arguments to generate a collision-resistant key.

---

## Validation / Acceptance Criteria

1. **Container Check:** Run `docker-compose ps` to ensure `bootcamp_redis` is healthy.
2. **First Load (Cache Miss):** Visit the Stock Overview page. The first load should take a few seconds as it reaches out to yfinance.
3. **Second Load (Cache Hit):** Switch pages and return, or refresh the Streamlit app. The load should be near instantaneous.
4. **Inspect Redis:**
   ```bash
   docker exec -it bootcamp_redis redis-cli
   127.0.0.1:6379> KEYS *
   ```
   You should see keys starting with `prices:` corresponding to the requested stock symbols.

---

## Next Steps

With our caching layer distributed, we are ready to move from local/Docker databases to cloud infrastructure.

Proceed to [Phase 7: Snowflake Cloud Data Warehouse](PHASE_7_SNOWFLAKE.md).
