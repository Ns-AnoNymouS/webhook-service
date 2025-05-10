import logging
import uuid

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from ..cache import (
    get_cached_subscription,
    set_cached_subscription,
    invalidate_cached_subscription,
)
from ..subscriptions.models import (
    create_subscription,
    delete_subscription,
    get_subscription,
    list_subscriptions,
    update_subscription,
)
from ..subscriptions.schemas import (
    SubscriptionCreate,
    SubscriptionOut,
    SubscriptionUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=SubscriptionOut)
async def add_subscription(payload: SubscriptionCreate):
    subscription_id = str(uuid.uuid4())  # unique ID for subscription
    subscription_data = payload.model_dump(mode="json")
    subscription_data["_id"] = subscription_id

    await create_subscription(subscription_data)  # Insert into MongoDB
    await set_cached_subscription(
        subscription_id, subscription_data
    )  # Cache the subscription data
    response_data = {"_id": subscription_id, **payload.model_dump(mode="json")}
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=response_data)


@router.get("/{subscription_id}", response_model=SubscriptionOut)
async def read_subscription(subscription_id: str):
    # 1. Try cache first
    cached = await get_cached_subscription(subscription_id)
    if cached:
        logger.info(f"Cache hit for subscription {subscription_id}")
        return cached

    # 2. Fetch from DB
    subscription = await get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # 3. Cache the result
    await set_cached_subscription(subscription_id, subscription)
    logger.info(f"Cache miss for subscription {subscription_id}, fetched from DB")
    return subscription


@router.get("", response_model=list[SubscriptionOut])
async def list_all_subscriptions():
    return await list_subscriptions()


@router.put("/{subscription_id}", response_model=SubscriptionOut)
async def edit_subscription(subscription_id: str, payload: SubscriptionUpdate):
    subscription = await get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    payload_data = payload.model_dump(mode="json")
    subscription_data = {k: v for k, v in payload_data.items() if v is not None}
    if not subscription_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    await update_subscription(subscription_id, subscription_data)  # Update in MongoDB
    updated = await get_subscription(subscription_id)
    await set_cached_subscription(subscription_id, updated)  # Update the cache
    return updated


@router.delete("/{subscription_id}")
async def remove_subscription(subscription_id: str):
    sub = await get_subscription(subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    logging.info(f"Deleting subscription {subscription_id}")
    await delete_subscription(subscription_id)  # delete from MongoDB
    await invalidate_cached_subscription(subscription_id)  # delete from cache
    return {"detail": f"Subscription {subscription_id} deleted"}
