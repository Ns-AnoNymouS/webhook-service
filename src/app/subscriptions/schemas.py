from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl

class SubscriptionCreate(BaseModel):
    target_url: HttpUrl
    event_types: List[str]
    secret: Optional[str] = None

class SubscriptionOut(SubscriptionCreate):
    id: str = Field(..., alias="_id")

class SubscriptionUpdate(BaseModel):
    target_url: Optional[HttpUrl] = None
    event_types: Optional[List[str]] = None
    secret: Optional[str] = None
