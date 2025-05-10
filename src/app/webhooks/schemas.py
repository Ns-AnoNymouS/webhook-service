from typing import Any, Dict, List, Optional

from pydantic import BaseModel

class EventTypeRequest(BaseModel):
    event_type: List[str]
    # Allow any additional arbitrary fields to be included in the payload
    payload: Optional[Dict[str, Any]] = None
