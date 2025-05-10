import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.main import app  # Adjust if your app is named differently

@pytest.fixture
def client():
    return TestClient(app)