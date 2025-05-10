import logging
import uuid
from fastapi import APIRouter, HTTPException, status, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

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
router = APIRouter(tags=["Subscriptions"])


class ErrorResponse(BaseModel):
    detail: str = Field(..., example="Subscription not found")


@router.post(
    "",
    response_model=SubscriptionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new subscription",
    description="Create and store a new webhook subscription.",
    response_description="The created subscription",
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def add_subscription(payload: SubscriptionCreate):
    subscription_id = str(uuid.uuid4())
    subscription_data = payload.model_dump(mode="json")
    subscription_data["_id"] = subscription_id

    await create_subscription(subscription_data)

    response_data = {"_id": subscription_id, **payload.model_dump(mode="json")}
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=response_data)


@router.get(
    "/{subscription_id}",
    response_model=SubscriptionOut,
    summary="Get a subscription by ID",
    description="Fetch subscription details by its unique ID.",
    response_description="Subscription object",
    responses={
        404: {"model": ErrorResponse, "description": "Subscription not found"},
        422: {"model": ErrorResponse, "description": "Invalid subscription ID"},
    },
)
async def read_subscription(
    subscription_id: str = Path(..., description="The subscription's unique ID")
):
    subscription = await get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return subscription


@router.get(
    "",
    response_model=list[SubscriptionOut],
    summary="List all subscriptions",
    description="Retrieve a list of all active webhook subscriptions.",
    response_description="List of subscriptions",
)
async def list_all_subscriptions():
    return await list_subscriptions()


@router.put(
    "/{subscription_id}",
    # response_model=SubscriptionOut,
    summary="Update a subscription",
    description="Update one or more fields of an existing subscription.",
    response_description="The updated subscription",
    responses={
        400: {"model": ErrorResponse, "description": "No fields to update"},
        404: {"model": ErrorResponse, "description": "Subscription not found"},
    },
)
async def edit_subscription(
    subscription_id: str = Path(..., description="The subscription's unique ID"),
    payload: SubscriptionUpdate = ...,
):
    subscription = await get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    payload_data = payload.model_dump(mode="json")
    subscription_data = {k: v for k, v in payload_data.items() if v is not None}

    if not subscription_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    await update_subscription(subscription_id, subscription_data)
    updated = await get_subscription(subscription_id)
    return updated


@router.delete(
    "/{subscription_id}",
    summary="Delete a subscription",
    description="Delete an existing webhook subscription using its ID.",
    response_description="Deletion confirmation message",
    responses={
        404: {"model": ErrorResponse, "description": "Subscription not found"},
    },
)
async def remove_subscription(
    subscription_id: str = Path(..., description="The subscription's unique ID")
):
    sub = await get_subscription(subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    logger.info(f"Deleting subscription {subscription_id}")
    await delete_subscription(subscription_id)

    return {"detail": f"Subscription {subscription_id} deleted"}
