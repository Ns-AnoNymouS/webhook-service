import asyncio
import logging
from datetime import datetime, timedelta, timezone

from ..config import WORKER_COUNT
from .tasks import send_webhook_task
from ..database import db

logger = logging.getLogger(__name__)

# Global event to signal shutdown
stop_event = asyncio.Event()

def start_workers(queue: asyncio.Queue):
    for _ in range(WORKER_COUNT):
        asyncio.create_task(worker_task(queue))
    logger.info(f"Started {WORKER_COUNT} workers")
    
    asyncio.create_task(delete_old_logs_periodically())
    logger.info("Started periodic task to delete old logs")


def stop_workers(queue: asyncio.Queue):
    logger.info("Stopping workers...")
    stop_event.set()  # Trigger shutdown signal for periodic tasks
    for _ in range(WORKER_COUNT):
        queue.put_nowait(None)


async def worker_task(queue: asyncio.Queue):
    while True:
        data = await queue.get()
        if data is None:
            return
        logger.info(f"Recieced task from queue with sub_id: {data['sub_id']}")
        await send_webhook_task(
            data["sub_id"],
            data["payload"],
            data["event_types"],
        )
        queue.task_done()

async def delete_old_logs_periodically():
    while not stop_event.is_set():
        try:
            threshold_time = datetime.now(timezone.utc) - timedelta(hours=72)
            result = await db.delivery_logs.delete_many({"created_at": {"$lt": threshold_time}})
            logger.info(f"Deleted {result.deleted_count} delivery logs older than 72 hours")
        except Exception as e:
            logger.error(f"Error deleting old logs: {e}")

        try:
            # Wait up to 1 hour, but break early if stop_event is set
            await asyncio.wait_for(stop_event.wait(), timeout=3600)
        except asyncio.TimeoutError:
            pass  # Continue loop after 1 hour