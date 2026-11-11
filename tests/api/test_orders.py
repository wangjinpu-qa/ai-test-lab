from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
def test_login_success(client: TestClient):
    response = client.post("/api/auth/login", json={"username": "tester", "password": "test123"})
    assert response.status_code == 200
    assert response.json()["code"] == "0000"
    assert response.json()["data"]["username"] == "tester"


@pytest.mark.api
def test_login_failure(client: TestClient):
    response = client.post("/api/auth/login", json={"username": "tester", "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"


@pytest.mark.api
def test_local_file_page_can_call_api_with_cors(client: TestClient):
    response = client.options(
        "/api/auth/login",
        headers={"Origin": "null", "Access-Control-Request-Method": "POST"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "null"


@pytest.mark.api
def test_list_orders_is_scoped_to_current_user(client: TestClient, auth_headers: dict[str, str]):
    response = client.get("/api/orders", headers=auth_headers)
    assert response.status_code == 200
    assert [row["id"] for row in response.json()["data"]] == ["ORD-1001", "ORD-1002"]


@pytest.mark.api
def test_pay_order_success(client: TestClient, auth_headers: dict[str, str], order_id: str):
    response = client.post(
        f"/api/orders/{order_id}/pay",
        headers=auth_headers,
        json={"amount": 98.0},
    )
    assert response.status_code == 200
    assert response.json()["code"] == "0000"
    assert response.json()["data"]["status"] == "PAID"
    assert response.json()["data"]["paid_amount"] == 98.0


@pytest.mark.api
def test_duplicate_payment_is_rejected(client: TestClient, auth_headers: dict[str, str], order_id: str):
    client.post(f"/api/orders/{order_id}/pay", headers=auth_headers, json={"amount": 98.0})
    response = client.post(f"/api/orders/{order_id}/pay", headers=auth_headers, json={"amount": 98.0})
    assert response.status_code == 409
    assert response.json()["code"] == "ORDER_ALREADY_PAID"


@pytest.mark.api
def test_unauthed_user_cannot_pay(client: TestClient, order_id: str):
    response = client.post(f"/api/orders/{order_id}/pay", json={"amount": 98.0})
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "UNAUTHORIZED"


@pytest.mark.api
def test_wrong_amount_is_rejected(client: TestClient, auth_headers: dict[str, str], order_id: str):
    response = client.post(f"/api/orders/{order_id}/pay", headers=auth_headers, json={"amount": 1.0})
    assert response.status_code == 400
    assert response.json()["code"] == "AMOUNT_MISMATCH"


@pytest.mark.api
def test_user_cannot_read_another_users_order(client: TestClient, auth_headers: dict[str, str]):
    response = client.get("/api/orders/ORD-1003", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["code"] == "ORDER_NOT_FOUND"
