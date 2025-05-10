import json
from typing import Optional

import redis.asyncio as redis

from .constants import CACHE_EXPIRY_SECONDS
from .config import REDIS_URL

# Initialize Redis client
redis_client = redis.from_url(REDIS_URL)

def cache_key_for_subscription(subscription_id: str) -> str:
    """
    Generate a standardized Redis key for a subscription.

    Args:
        subscription_id (str): The unique ID of the subscription.

    Returns:
        str: Namespaced Redis key.
    """
    return f"subscription:{subscription_id}"


async def get_cached_subscription(subscription_id: str) -> Optional[dict]:
    """
    Retrieve a cached subscription object from Redis.

    Args:
        subscription_id (str): The unique ID of the subscription.

    Returns:
        Optional[dict]: The cached subscription data if found, otherwise None.
    """
    key = cache_key_for_subscription(subscription_id)
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        print(f"Redis get error: {e}")
    return None


async def set_cached_subscription(
    subscription_id: str, data: Optional[dict], expiry: int = CACHE_EXPIRY_SECONDS
):
    """
    Store a subscription object in Redis with an expiry.

    Args:
        subscription_id (str): The unique ID of the subscription.
        data (Optional[dict]): Subscription data to cache.
        expiry (int, optional): Expiry time in seconds. Defaults to `CACHE_EXPIRY_SECONDS`.
    """
    key = cache_key_for_subscription(subscription_id)
    try:
        await redis_client.setex(key, expiry, json.dumps(data))
    except Exception as e:
        print(f"Redis set error: {e}")


async def invalidate_cached_subscription(subscription_id: str):
    """
    Invalidate (delete) a cached subscription from Redis.

    Args:
        subscription_id (str): The unique ID of the subscription.
    """
    key = cache_key_for_subscription(subscription_id)
    try:
        await redis_client.delete(key)
    except Exception as e:
        print(f"Redis delete error: {e}")
