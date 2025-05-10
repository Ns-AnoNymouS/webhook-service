from fastapi import FastAPI

from .delivery_logs.router import router as logs_router
from .subscriptions.router import router as subscriptions_router
from .webhooks.router import router as webhooks_router

import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Stream handler (prints to console)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(name)s: %(message)s")
handler.setFormatter(formatter)

logger.addHandler(handler)

app = FastAPI()

app.include_router(subscriptions_router, prefix="/subscriptions", tags=["Subscriptions"])
app.include_router(webhooks_router, prefix="/ingest", tags=["Webhook Ingestion"])
app.include_router(logs_router, prefix="/status", tags=["Delivery Logs"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Webhook Service"}