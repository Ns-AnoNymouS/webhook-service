from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Optional, List, Any


class Attempt(BaseModel):
    timestamp: datetime
    status_code: int
    success: bool
    attempt: int


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
