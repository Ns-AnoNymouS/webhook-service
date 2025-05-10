import json
import hmac
import logging
import asyncio
import hashlib
from uuid import uuid4
from typing import List
from datetime import datetime, timezone

from httpx import AsyncClient, HTTPStatusError, TimeoutException, ConnectError

from ..constants import RETRY_INTERVALS
from ..config import REQUEST_TIMEOUT
from ..subscriptions.models import get_subscription
from ..database import db

logger = logging.getLogger(__name__)


async def send_webhook_task(sub_id: str, payload: dict, event: List[str]):
    subscription = await get_subscription(sub_id, event_type=event)

    if not subscription:
        logger.warning(f"No subscription found for ID: {sub_id} and event: {event}")
        return

    logger.info(f"Sending webhook to {subscription['target_url']} for event(s): {event}")

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Event": ", ".join(event),
    }

    log_id = str(uuid4())
    log_entry = {
        "_id": log_id,
        "subscription_id": subscription["_id"],
        "target_url": subscription["target_url"],
        "event_types": subscription.get("event_types", []),
        "payload": payload,
        "attempts": [],
        "final_status": None,
        "created_at": datetime.now(timezone.utc),
    }

    # Add signature if secret is set
    if secret := subscription.get("secret"):
        body = json.dumps(payload).encode()
        signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        headers["X-Hub-Signature-256"] = f"sha256={signature}"

    async with AsyncClient() as client:
        for i, delay in enumerate(RETRY_INTERVALS + [0]):  # Final zero for delay before last retry
            attempt = {
                "timestamp": datetime.now(timezone.utc),
                "attempt": i + 1,
                "status_code": None,
                "success": False,
                "error": None,
            }

            try:
                response = await client.post(
                    subscription["target_url"],
                    json=payload,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                attempt["status_code"] = response.status_code
                attempt["success"] = True
                log_entry["attempts"].append(attempt)
                log_entry["final_status"] = "success"
                logger.info(f"Webhook sent successfully to {subscription['target_url']} (attempt {i + 1})")
                break  # Success, exit retry loop

            except TimeoutException:
                attempt["error"] = "Timeout"
                logger.warning(f"Webhook attempt {i + 1} timed out.")

            except ConnectError as exc:
                attempt["error"] = "Connection error"
                logger.warning(f"Webhook attempt {i + 1} connection error: {exc}")
                if "CERTIFICATE_VERIFY_FAILED" in str(exc):
                    attempt["error"] = "SSL certificate verification failed"
                    logger.error("SSL certificate verification failed. Aborting retries.")
                    log_entry["attempts"].append(attempt)
                    break

            except HTTPStatusError as exc:
                attempt["status_code"] = exc.response.status_code
                attempt["error"] = str(exc)
                logger.warning(f"Webhook attempt {i + 1} received HTTP error: {exc.response.status_code}")

            except Exception as exc:
                attempt["error"] = str(exc)
                logger.exception(f"Unexpected error during webhook attempt {i + 1}: {exc}")

            log_entry["attempts"].append(attempt)
            await asyncio.sleep(delay)

        else:
            log_entry["final_status"] = "failed"
            logger.error(f"All webhook attempts failed for subscription {sub_id}")

    result = await db.delivery_logs.insert_one(log_entry)
    logger.info(f"Delivery log saved with ID: {log_id}")
