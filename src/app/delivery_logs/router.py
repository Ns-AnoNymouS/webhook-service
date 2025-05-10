from fastapi import APIRouter
from ..delivery_logs.schemas import DeliveryLog
from ..database import db
from typing import List

router = APIRouter()
collection = db.delivery_logs


@router.get("/delivery-logs", response_model=List[DeliveryLog])
async def fetch_delivery_logs(limit: int = 10):
    if limit == -1:
        # Return all delivery logs if limit is -1
        logs = await collection.find({}).to_list(
            length=None
        )
    else:
        # Return limited number of delivery logs
        logs = await collection.find({}).to_list(
            length=limit
        )

    # Convert the MongoDB data to DeliveryLog schema objects
    delivery_logs = [DeliveryLog(**log) for log in logs]
    return delivery_logs
