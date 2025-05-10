import asyncio
import logging
from datetime import datetime, timedelta, timezone

from ..config import WORKER_COUNT
from .tasks import send_webhook_task
from ..database import db

logger = logging.getLogger(__name__)

# Global event to signal shutdown
stop_event = asyncio.Event()

# Keep track of background tasks for graceful shutdown if needed
background_tasks = []


def start_workers(queue: asyncio.Queue):
    for i in range(WORKER_COUNT):
        task = asyncio.create_task(worker_task(f"Worker-{i+1}", queue))
        background_tasks.append(task)

    logger.info(f"Started {WORKER_COUNT} webhook workers")

    # Start log cleanup task
    cleanup_task = asyncio.create_task(delete_old_logs_periodically())
    background_tasks.append(cleanup_task)
    logger.info("Started periodic log cleanup task")


def stop_workers(queue: asyncio.Queue):
    logger.info("Stopping workers...")
    stop_event.set()  # Trigger shutdown signal for periodic tasks

    # Add None to the queue to stop workers
    for _ in range(WORKER_COUNT):
        queue.put_nowait(None)


async def worker_task(name: str, queue: asyncio.Queue):
    while True:
        data = await queue.get()

        if data is None:
            logger.info(f"{name} received shutdown signal. Exiting.")
            queue.task_done()
            return

        logger.info(
            f"Received task from queue by {name} | sub_id: {data['sub_id']} | queue size: {queue.qsize()}"
        )

        try:
            await send_webhook_task(
                data["sub_id"],
                data["payload"],
                data["event_types"],
            )
        except Exception as e:
            logger.exception(f"Unexpected error during task execution: {e}")

        queue.task_done()


async def delete_old_logs_periodically():
    while not stop_event.is_set():
        try:
            threshold_time = datetime.now(timezone.utc) - timedelta(hours=72)
            result = await db.delivery_logs.delete_many(
                {"created_at": {"$lt": threshold_time}}
            )
            logger.info(
                f"Deleted {result.deleted_count} delivery logs older than 72 hours"
            )
        except Exception as e:
            logger.error(f"Error deleting old logs: {e}")

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=3600)
        except asyncio.TimeoutError:
            continue  # Run cleanup again after 1 hour


async def wait_for_background_tasks():
    """Waits for all background tasks to complete (for graceful shutdown)."""
    await asyncio.gather(*background_tasks, return_exceptions=True)
    logger.info("All background tasks completed.")
