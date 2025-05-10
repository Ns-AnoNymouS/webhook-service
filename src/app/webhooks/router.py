import logging

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse

from ..subscriptions.models import get_subscription
from ..webhooks.schemas import EventTypeRequest
from ..workers.tasks import send_webhook_task

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/{sub_id}")
async def ingest_webhook(
    sub_id: str,
    event_request: EventTypeRequest,  # Directly use EventTypeRequest as a parameter
    background_tasks: BackgroundTasks
):
    print(f"Received request to ingest webhook for subscription ID: {sub_id}")
    # Fetch subscription details using the sub_id
    sub = await get_subscription(sub_id)
    if not sub:
        return JSONResponse(status_code=404, content={"detail": "Subscription not found"})

    # If event_type is provided, validate that at least one of the event types exists in the subscription
    event_types = event_request.event_type
    if event_types and sub.get("event_types", []) and not any(event_type in sub.get("event_types", []) for event_type in event_types):
        return JSONResponse(status_code=403, content={"detail": "Event not subscribed"})

    # Extract the payload if provided
    payload = event_request.payload if event_request.payload else {}

    # Add the background task to send the webhook asynchronously
    background_tasks.add_task(send_webhook_task, sub_id=sub_id, payload=payload, event=event_types or [])

    # Log that the task was accepted and return the 202 Accepted response
    logger.info(f"Webhook task queued for subscription {sub_id} with event types: {event_types}")
    return JSONResponse(status_code=202, content={"detail": "Accepted"})