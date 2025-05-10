from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict


class Attempt(BaseModel):
    timestamp: datetime
    status_code: Optional[int]
    success: bool
    attempt: int
    error: Optional[str] = None


class DeliveryLog(BaseModel):
    attempts: List[Attempt]
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    delivery_id: str = Field(..., alias="_id")
    event_types: List[str]
    final_status: Optional[str] = (
        None  # Final status of the delivery (e.g., "success", "failed")
    )
    payload: Any  # Payload can be any structure
    subscription_id: str
    target_url: str


class RecentDeliveryResponse(BaseModel):
    delivery_id: str
    event_types: List[str]
    payload: Dict[str, Any]
    attempts: List[Attempt]
    status: str
    timestamp: str
