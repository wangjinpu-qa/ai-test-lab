from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app, reset_database


@pytest.fixture()
def client() -> TestClient:
    reset_database()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"username": "tester", "password": "test123"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['token']}"}


@pytest.fixture()
def order_id() -> str:
    return "ORD-1001"
