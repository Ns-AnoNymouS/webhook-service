import pytest
import asyncio
import aiohttp
from multiprocessing import Process
import uvicorn
from time import sleep
import respx
from httpx import AsyncClient, Response
from aioresponses import aioresponses
from fastapi.testclient import TestClient

# Start FastAPI app in background using uvicorn
def run_app():
    from app.main import app
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

@pytest.fixture(scope="session", autouse=True)
def start_fastapi_server():
    proc = Process(target=run_app, daemon=True)
    proc.start()
    sleep(3)  # Wait for server to be ready
    yield
    proc.terminate()

BASE_URL = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_create_subscription():
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE_URL}/subscriptions", json={
            "target_url": "https://test.com",
            "event_types": ["test.event"]
        }) as response:
            assert response.status == 201
            data = await response.json()
            assert "_id" in data
            assert data["target_url"] == "https://test.com/"
            assert set(data["event_types"]) == {"test.event"}

@pytest.mark.asyncio
async def test_create_subscription_invalid():
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE_URL}/subscriptions", json={
            "event_types": ["test.event"]
        }) as response:
            assert response.status == 422

@pytest.mark.asyncio
async def test_crud_lifecycle():
    async with aiohttp.ClientSession() as session:
        # Create
        async with session.post(f"{BASE_URL}/subscriptions", json={
            "target_url": "https://test.com",
            "event_types": ["test.event"]
        }) as create_resp:
            assert create_resp.status == 201
            created = await create_resp.json()
            sub_id = created["_id"]

        # Read
        async with session.get(f"{BASE_URL}/subscriptions/{sub_id}") as get_resp:
            assert get_resp.status == 200

        # Update
        async with session.put(f"{BASE_URL}/subscriptions/{sub_id}", json={
            "target_url": "https://updated.com",
            "event_types": ["updated.event"]
        }) as update_resp:
            assert update_resp.status == 200
            updated = await update_resp.json()
            assert updated["target_url"] == "https://updated.com/"
            assert updated["event_types"] == ["updated.event"]

        # Delete
        async with session.delete(f"{BASE_URL}/subscriptions/{sub_id}") as delete_resp:
            assert delete_resp.status == 200

        # Confirm Deletion
        async with session.get(f"{BASE_URL}/subscriptions/{sub_id}") as confirm_resp:
            assert confirm_resp.status == 404

@pytest.mark.asyncio
async def test_update_nonexistent_subscription():
    async with aiohttp.ClientSession() as session:
        async with session.put(f"{BASE_URL}/subscriptions/663d6b5c72a4f72a1fdf9999", json={
            "target_url": "https://fail.com",
            "event_types": ["fail"]
        }) as response:
            assert response.status == 404

@pytest.mark.asyncio
async def test_delete_nonexistent_subscription():
    async with aiohttp.ClientSession() as session:
        async with session.delete(f"{BASE_URL}/subscriptions/663d6b5c72a4f72a1fdf9999") as response:
            assert response.status == 404
  

# @pytest.mark.asyncio
# async def test_webhook_triggered_with_respx():
#     target_url = "https://webhook.site/test-endpoint"

#     # Mock the external webhook URL without using context manager
#     respx_mock = respx.mock(base_url="https://webhook.site")
    
#     # Mock external webhook request
#     webhook_route = respx_mock.post("/test-endpoint").mock(
#         return_value=Response(200, json={"received": True})
#     )

#     # HTTPX client for FastAPI app running at BASE_URL
#     async with AsyncClient(base_url=BASE_URL) as client:
#         # Create a subscription for event type "order.update"
#         resp = await client.post("/subscriptions", json={
#             "target_url": target_url,
#             "event_types": ["order.update"]
#         })
#         assert resp.status_code == 201

#         body = resp.json()
#         sub_id = body["_id"]

#         # Trigger the webhook by sending an event to the FastAPI app
#         trigger_resp = await client.post(f"/ingest/{sub_id}", json={
#             "event_type": ["order.update"],
#             "payload": {"order_id": "1234", "status": "shipped"}
#         })
#         assert trigger_resp.status_code == 202

#     timeout = 5  # Max wait time in seconds
#     elapsed_time = 0
#     while elapsed_time < timeout and webhook_route.call_count == 0:
#         await asyncio.sleep(1)  # Wait 1 second before checking again
#         elapsed_time += 1

#     # Confirm the webhook was sent to the external endpoint
#     assert webhook_route.called
#     assert webhook_route.call_count == 1

#     # Close the respx mock to ensure cleanup
#     respx_mock.close()