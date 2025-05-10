import json
import hmac
import logging
import asyncio
import hashlib
from uuid import uuid4
from typing import List
from datetime import datetime, timezone

from httpx import AsyncClient, HTTPStatusError

from ..constants import RETRY_INTERVALS
from ..subscriptions.models import get_subscription
from ..database import db

logger = logging.getLogger(__name__)


async def send_webhook_task(sub_id: str, payload: dict, event: List[str]):
    subscription = await get_subscription(sub_id, event_type=event)
    logger.info(f"Sending webhook to {subscription} for event {event}")
    if not subscription:
        return

    headers = {"Content-Type": "application/json", "X-Webhook-Event": event}
    # Ensure all header values are strings (no lists or other types)
    headers = {
        key: str(value) if not isinstance(value, list) else ", ".join(value)
        for key, value in headers.items()
    }

    log_id = str(uuid4())
    log_entry = {
        "_id": log_id,
        "subscription_id": subscription["_id"],
        "target_url": subscription["target_url"],
        "event_types": subscription["event_types"],
        "payload": payload,
        "attempts": [],
        "final_status": None,
        "created_at": datetime.now(timezone.utc),
    }

    if subscription.get("secret"):
        body = json.dumps(payload).encode()
        signature = hmac.new(
            subscription["secret"].encode(), body, hashlib.sha256
        ).hexdigest()
        headers["X-Hub-Signature-256"] = f"sha256={signature}"

    async with AsyncClient() as client:
        retries = RETRY_INTERVALS + [
            0
        ]  # Adding a final zero to ensure we wait before final attempt
        for i, retry_in in enumerate(retries):
            try:
                response = await client.post(
                    subscription["target_url"],
                    json=payload,
                    headers=headers,
                    timeout=10.0,
                )
                status = response.status_code
                response.raise_for_status()
                success = True
                logger.info(f"Webhook sent successfully on attempt {i+1}")
            except HTTPStatusError as exc:
                success = False
                status = exc.response.status_code
                logger.warning(f"Attempt {i+1} failed: {exc}")
                if i == len(RETRY_INTERVALS) - 1:
                    logger.error("Max retries reached, giving up.")

            attempt_data = {
                "timestamp": datetime.now(timezone.utc),
                "status_code": status,
                "success": success,
                "attempt": i + 1,
            }

            log_entry["attempts"].append(attempt_data)
            if success:
                log_entry["final_status"] = "success"
                break
            else:
                await asyncio.sleep(retry_in)

        else:
            log_entry["final_status"] = "failed"

    status = await db.delivery_logs.insert_one(log_entry)
    print("Updated delivery log with status:", status)
