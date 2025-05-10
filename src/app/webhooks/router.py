import hmac
import hashlib
import json
import logging
from typing import List, Dict, Any

from fastapi import Request, BackgroundTasks, Query, Body, APIRouter, Header
from fastapi.responses import JSONResponse

from ..subscriptions.models import get_subscription

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/{sub_id}")
async def ingest_webhook(
    sub_id: str,
    background_tasks: BackgroundTasks,
    request: Request,
    body: Dict[str, Any] = Body(..., media_type="application/json"),
    event_types: List[str] = Query(default=[]),
    x_hub_signature_256: str = Header(default=None, convert_underscores=False),
):
    logger.info(f"Received request to ingest webhook for subscription ID: {sub_id}")

    sub = await get_subscription(sub_id)
    if not sub:
        return JSONResponse(status_code=404, content={"detail": "Subscription not found"})

    if sub.get("secret"):
        if not x_hub_signature_256:
            return JSONResponse(status_code=403, content={"detail": "Missing signature"})
        
        body_bytes = json.dumps(body, separators=(",", ":")).encode()
        # Generate the expected signature
        expected_signature = hmac.new(
            sub["secret"].encode(), body_bytes, hashlib.sha256
        ).hexdigest()

        full_expected = f"sha256={expected_signature}"
        if x_hub_signature_256 != full_expected:
            logger.warning(f"Signature mismatch: expected {full_expected}, got {x_hub_signature_256}")
            return JSONResponse(status_code=403, content={"detail": "Invalid signature"})

    # Validate event types if subscription limits them
    if event_types:
        allowed_types = sub.get("event_types", [])
        if allowed_types and not any(et in allowed_types for et in event_types):
            return JSONResponse(status_code=403, content={"detail": "Event not subscribed"})

    # Add webhook task to background queue
    request.app.state.queue.put_nowait(
        {
            "sub_id": sub_id,
            "payload": body,
            "event_types": event_types or [],
        }
    )

    logger.info(f"Webhook task queued for subscription {sub_id} with event types: {event_types}")
    return JSONResponse(status_code=202, content={"detail": "Accepted"})
