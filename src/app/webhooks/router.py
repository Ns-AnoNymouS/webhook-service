import hmac
import hashlib
import json
import logging
from typing import List, Dict, Any, Optional

from fastapi import (
    Request,
    Query,
    Body,
    APIRouter,
    Header,
)
from fastapi.responses import JSONResponse

from ..subscriptions.models import get_subscription

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Webhook Ingestion"])


@router.post(
    "/{sub_id}",
    summary="Ingest webhook event",
    description=(
        "Accepts a webhook payload for a given subscription ID. If a secret is configured for the subscription, "
        "the request must be signed using HMAC-SHA256 and included in the `X-Hub-Signature-256` header. "
        "The endpoint supports optional event type validation and queues the webhook for background processing."
    ),
    response_description="Webhook accepted and queued",
    responses={
        202: {"description": "Accepted"},
        403: {"description": "Invalid or missing signature / Event not subscribed"},
        404: {"description": "Subscription not found"},
        422: {"description": "Validation error"},
    },
)
async def ingest_webhook(
    sub_id: str,
    request: Request,
    body: Dict[str, Any] = Body(..., media_type="application/json"),
    event_types: List[str] = Query(
        default=[], description="List of event types being sent in this webhook. Leave empty to trigger all events."
    ),
    x_hub_signature_256: Optional[str] = Header(
        default=None,
        convert_underscores=False,
        description="HMAC SHA256 signature in the format: sha256=<digest>",
    ),
) -> JSONResponse:
    """
    Ingests a webhook request for a given subscription.

    Args:
        sub_id (str): Subscription ID that identifies the webhook subscription.
        background_tasks (BackgroundTasks): FastAPI background task handler.
        request (Request): Incoming HTTP request object.
        body (Dict[str, Any]): JSON payload of the webhook.
        event_types (List[str]): Optional list of event types included in the payload.
        x_hub_signature_256 (Optional[str]): Optional HMAC-SHA256 signature header.

    Returns:
        JSONResponse: Status 202 if accepted, or appropriate error message otherwise.
    """
    logger.info(f"Received request to ingest webhook for subscription ID: {sub_id}")

    sub = await get_subscription(sub_id)
    if not sub:
        logger.warning(f"No subscription found for ID: {sub_id}")
        return JSONResponse(
            status_code=404, content={"detail": "Subscription not found"}
        )

    if sub.get("secret"):
        if not x_hub_signature_256:
            return JSONResponse(
                status_code=403, content={"detail": "Missing signature"}
            )

        body_bytes = json.dumps(body, separators=(",", ":")).encode()
        expected_signature = hmac.new(
            sub["secret"].encode(), body_bytes, hashlib.sha256
        ).hexdigest()
        full_expected = f"sha256={expected_signature}"

        if x_hub_signature_256 != full_expected:
            logger.warning(
                f"Signature mismatch: expected {full_expected}, got {x_hub_signature_256}"
            )
            return JSONResponse(
                status_code=403, content={"detail": "Invalid signature"}
            )

    if event_types:
        allowed_types = sub.get("event_types", [])
        if allowed_types and not any(et in allowed_types for et in event_types):
            logger.warning(
                f"Rejected event types {event_types}; allowed: {allowed_types}"
            )
            return JSONResponse(
                status_code=403, content={"detail": "Event not subscribed"}
            )

    # Add webhook task to background queue
    logger.info(
        f"Webhook task queued for subscription {sub_id} with event types: {event_types}"
    )
    request.app.state.queue.put_nowait(
        {
            "sub_id": sub_id,
            "payload": body,
            "event_types": event_types or [],
        }
    )

    return JSONResponse(status_code=202, content={"detail": "Accepted"})
