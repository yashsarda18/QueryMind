import redis
import json
import hashlib
import os
import logging

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=2, socket_timeout=2)

CACHE_TTL_SECONDS = 3600


def normalize_question(question: str) -> str:
    return " ".join(question.lower().split())


def get_cache_key(question: str) -> str:
    normalized = normalize_question(question)
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


def get_cached_result(question: str):
    key = get_cache_key(question)
    try:
        cached = r.get(key)
    except redis.ConnectionError:
        logger.warning("Redis unavailable — skipping cache lookup, treating as cache miss")
        return None
    if cached is None:
        return None
    return json.loads(cached)


def set_cached_result(question: str, result: dict):
    key = get_cache_key(question)
    try:
        r.set(key, json.dumps(result, default=str), ex=CACHE_TTL_SECONDS)
    except redis.ConnectionError:
        logger.warning("Redis unavailable — skipping cache write, result not cached")


def check_rate_limit(client_id: str, max_requests: int = 20, window_seconds: int = 60) -> bool:
    key = f"ratelimit:{client_id}"
    try:
        count = r.incr(key)
        if count == 1:
            r.expire(key, window_seconds)
        return count <= max_requests
    except redis.ConnectionError:
        logger.warning("Redis unavailable — failing open, rate limit not enforced for this request")
        return True