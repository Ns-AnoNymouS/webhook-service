from fastapi import APIRouter, Query, Path, HTTPException
from typing import List

from pydantic import BaseModel, Field

from ..delivery_logs.schemas import DeliveryLog, RecentDeliveryResponse
from ..database import db

router = APIRouter(tags=["Delivery Logs"])
collection = db.delivery_logs


class ErrorResponse(BaseModel):
    detail: str = Field(..., example="Delivery log not found")


@router.get(
    "/delivery-logs",
    response_model=List[DeliveryLog],
    summary="Fetch delivery logs",
    description="Retrieve a list of webhook delivery logs. Use `limit=-1` to fetch all logs.",
    response_description="List of delivery log entries",
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def fetch_delivery_logs(
    limit: int = Query(10, description="Number of logs to return. Use -1 to fetch all.")
) -> List[DeliveryLog]:
    """
    Fetch a list of delivery logs, sorted by most recent.

    Args:
        limit (int): Number of logs to return. -1 returns all logs.

    Returns:
        List[DeliveryLog]: List of delivery log entries.
    """
    if limit == -1:
        logs = await collection.find({}).sort("created_at", -1).to_list(length=None)
    else:
        logs = await collection.find({}).sort("created_at", -1).to_list(length=limit)

    return [DeliveryLog(**log) for log in logs]


@router.get(
    "/delivery/{delivery_id}",
    response_model=DeliveryLog,
    summary="Get delivery log by ID",
    description="Fetch a specific delivery log using its unique delivery ID.",
    response_description="Single delivery log object",
    responses={
        404: {"model": ErrorResponse, "description": "Delivery log not found"},
        422: {"model": ErrorResponse, "description": "Invalid delivery ID"},
    },
)
async def get_delivery_status(
    delivery_id: str = Path(..., description="The unique delivery ID")
) -> DeliveryLog:
    """
    Get details of a specific delivery log by its ID.

    Args:
        delivery_id (str): The unique ID of the delivery log.

    Returns:
        DeliveryLog: Delivery log object if found.
    """
    log = await collection.find_one({"_id": delivery_id})
    if not log:
        raise HTTPException(status_code=404, detail="Delivery log not found")
    return DeliveryLog(**log)


@router.get(
    "/delivery/subscription/{sub_id}",
    response_model=List[RecentDeliveryResponse],
    summary="Get recent deliveries for a subscription",
    description="Retrieve recent webhook deliveries for a given subscription ID, ordered by creation time.",
    response_description="List of recent deliveries",
    responses={
        422: {
            "model": ErrorResponse,
            "description": "Invalid subscription ID or query param",
        },
    },
)
async def get_recent_deliveries(
    sub_id: str = Path(..., description="The subscription ID"),
    limit: int = Query(20, description="Number of recent deliveries to return"),
) -> List[RecentDeliveryResponse]:
    """
    Get recent webhook deliveries for a subscription.

    Args:
        sub_id (str): Subscription ID to filter logs.
        limit (int): Maximum number of logs to return.

    Returns:
        List[RecentDeliveryResponse]: List of recent delivery summaries.
    """
    cursor = (
        collection.find({"subscription_id": sub_id}).sort("created_at", -1).limit(limit)
    )
    logs = await cursor.to_list(length=limit)

    return [
        RecentDeliveryResponse(
            delivery_id=log["_id"],
            event_types=log["event_types"],
            payload=log["payload"],
            attempts=log["attempts"],
            status=log["final_status"],
            timestamp=log["created_at"].strftime("%Y-%m-%d %H:%M:%S"),
        )
        for log in logs
    ]
