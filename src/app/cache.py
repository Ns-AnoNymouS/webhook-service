import json
from typing import Optional

import redis.asyncio as redis

from .constants import CACHE_EXPIRY_SECONDS
from .config import REDIS_URL

redis_client = redis.from_url(REDIS_URL)

async def get_cached_subscription(subscription_id: str) -> Optional[dict]:
    key = f"subscription:{subscription_id}"
    data = await redis_client.get(key)
    if data:
        return json.loads(data)
    return None

async def set_cached_subscription(subscription_id: str, data: Optional[dict]):
    key = f"subscription:{subscription_id}"
    await redis_client.setex(key, CACHE_EXPIRY_SECONDS, json.dumps(data))

async def invalidate_cached_subscription(subscription_id: str):
    key = f"subscription:{subscription_id}"
    await redis_client.delete(key)
