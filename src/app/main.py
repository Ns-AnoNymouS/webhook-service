import logging
import asyncio

from fastapi import FastAPI
from contextlib import asynccontextmanager

from .delivery_logs.router import router as logs_router
from .subscriptions.router import router as subscriptions_router
from .webhooks.router import router as webhooks_router
from .workers.service import start_workers, stop_workers, wait_for_background_tasks

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Stream handler (prints to console)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(name)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.queue = asyncio.Queue(maxsize=1000)  # optional: cap queue size
    start_workers(app.state.queue)
    yield
    logger.info("Shutting down...")
    stop_workers(app.state.queue)
    await wait_for_background_tasks()

app = FastAPI(lifespan=lifespan)

app.include_router(subscriptions_router, prefix="/subscriptions", tags=["Subscriptions"])
app.include_router(webhooks_router, prefix="/ingest", tags=["Webhook Ingestion"])
app.include_router(logs_router, prefix="/status", tags=["Delivery Logs"])


@app.get("/")
def read_root():
    return {"message": "Welcome to the Webhook Service"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
