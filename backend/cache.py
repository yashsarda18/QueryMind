import redis
import json
import hashlib

r = redis.Redis(host='localhost', port=6379, decode_responses=True)
CACHE_TTL_SECONDS = 3600

def normalize_question(question: str) -> str:
    return " ".join(question.lower().split())

def get_cache_key(question: str) -> str:
    normalized = normalize_question(question)
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()

def get_cached_result(question: str):
    key = get_cache_key(question)
    cached = r.get(key)
    if cached is None:
        return None
    return json.loads(cached)

def set_cached_result(question: str, result: dict):
    key = get_cache_key(question)
    r.set(key, json.dumps(result, default=str), ex=CACHE_TTL_SECONDS)
    
def check_rate_limit(client_id: str, max_requests: int = 20, window_seconds: int = 60) -> bool:
    key = f"ratelimit:{client_id}"
    count = r.incr(key)
    if count == 1:
        r.expire(key, window_seconds)
    return count <= max_requests