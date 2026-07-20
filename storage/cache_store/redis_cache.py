import os
import json
import hashlib
from redis import Redis
from dotenv import load_dotenv

load_dotenv()

_redis_url = os.getenv("REDIS_URL")
if _redis_url:
    # cloud (upstash) - one URL bundles host, port, password, and TLS.
    _redis = Redis.from_url(_redis_url, decode_responses=True)
else:
    # Local Docker -Seperate host/port , no password, no TLS
    _redis = Redis(
        host=os.getenv("REDIS_HOST"),
        port=int(os.getenv("REDIS_PORT")),
        decode_responses=True,
    )


def _make_cache_key(
    question: str, user_id: str, org_id: str, document_id: str = None
) -> str:
    """
    Builds a cache key that includes the full scope of the query,
    not just the question text. This is what prevents alice's cached answer from ever being served to Bob - the tennacy
    boundary applies to caching exactly as strictly as it applies
    to retrieval , sice a cache is just another kind of read path.
    """
    raw = f"{user_id}:{org_id}:{document_id or 'all'}:{question.lower().strip()}"
    return "query_cache:" + hashlib.sha256(raw.encode()).hexdigest()


def get_cached_answer(
    question: str, user_id: str, org_id: str, document_id: str = None
) -> dict | None:
    key = _make_cache_key(question, user_id, org_id, document_id)
    cached = _redis.get(key)
    if cached is None:
        return None
    return json.loads(cached)


def set_cached_answer(
    question: str,
    user_id: str,
    org_id: str,
    result: dict,
    document_id: str = None,
    ttl_seconds: int = 3600,
) -> None:
    key = _make_cache_key(question, user_id, org_id, document_id)
    _redis.setex(key, ttl_seconds, json.dumps(result))
