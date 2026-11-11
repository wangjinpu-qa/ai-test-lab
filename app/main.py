"""Small local order service used by the AI testing lab.

The service deliberately keeps the business model small so that the test
automation and AI-assisted workflows remain easy to inspect.
"""

from __future__ import annotations

import os
import secrets
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("DB_PATH", str(ROOT / "data" / "orders.db")))
WEB_DIR = Path(__file__).resolve().parent / "web"
TOKENS: Dict[str, str] = {}


class LoginRequest(BaseModel):
    username: str
    password: str


class PayRequest(BaseModel):
    amount: Optional[float] = None


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _seed_orders(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            customer TEXT NOT NULL,
            item TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            paid_amount REAL,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
        """
    )
    connection.execute(
        "INSERT OR REPLACE INTO users(username, password, role) VALUES (?, ?, ?)",
        ("tester", "test123", "tester"),
    )
    connection.commit()


def reset_database() -> None:
    """Reset local data to a deterministic state for repeatable tests."""

    with _connect() as connection:
        _seed_orders(connection)
        connection.execute("DELETE FROM orders")
        connection.executemany(
            """
            INSERT INTO orders(id, customer, item, amount, status, paid_amount, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("ORD-1001", "tester", "Keyboard", 98.00, "CREATED", None, "2026-01-01T09:00:00Z"),
                ("ORD-1002", "tester", "Mouse", 39.90, "CREATED", None, "2026-01-01T09:05:00Z"),
                ("ORD-1003", "other-user", "Monitor", 299.00, "CREATED", None, "2026-01-01T09:10:00Z"),
            ],
        )
        connection.commit()


def _order_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def _current_user(authorization: Optional[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "登录已失效"})
    username = TOKENS.get(authorization[7:])
    if not username:
        raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "登录已失效"})
    return username


def _response(code: str, data: Any = None, message: str = "") -> Dict[str, Any]:
    return {"code": code, "message": message, "data": data}


def _bootstrap() -> None:
    with _connect() as connection:
        _seed_orders(connection)
        count = connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        if count == 0:
            connection.commit()
            reset_database()


_bootstrap()
app = FastAPI(title="AI Test Lab Order API", version="1.0.0")
# The demo page is sometimes opened directly as a ``file://`` URL while
# learning locally. Allow only local development origins, including the
# browser's ``null`` origin for file URLs. This is intentionally not enabled
# for non-local environments.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000", "null"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/login", include_in_schema=False)
def login_page() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.post("/api/auth/login")
def login(payload: LoginRequest) -> Dict[str, Any]:
    with _connect() as connection:
        user = connection.execute(
            "SELECT username, role FROM users WHERE username=? AND password=?",
            (payload.username, payload.password),
        ).fetchone()
    if not user:
        return JSONResponse(
            status_code=401,
            content=_response("INVALID_CREDENTIALS", message="用户名或密码错误"),
        )
    token = secrets.token_urlsafe(24)
    TOKENS[token] = user["username"]
    return _response("0000", {"token": token, "username": user["username"], "role": user["role"]})


@app.get("/api/orders")
def list_orders(
    authorization: Optional[str] = Header(default=None),
    keyword: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    username = _current_user(authorization)
    sql = "SELECT * FROM orders WHERE customer=?"
    params: list[Any] = [username]
    if keyword:
        sql += " AND (id LIKE ? OR item LIKE ?)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    sql += " ORDER BY id"
    with _connect() as connection:
        rows = connection.execute(sql, params).fetchall()
    return _response("0000", [_order_dict(row) for row in rows])


@app.get("/api/orders/{order_id}")
def get_order(order_id: str, authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    username = _current_user(authorization)
    with _connect() as connection:
        row = connection.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not row or row["customer"] != username:
        return JSONResponse(
            status_code=404,
            content=_response("ORDER_NOT_FOUND", message="订单不存在"),
        )
    return _response("0000", _order_dict(row))


@app.post("/api/orders/{order_id}/pay")
def pay_order(
    order_id: str,
    payload: PayRequest,
    authorization: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    username = _current_user(authorization)
    with _connect() as connection:
        row = connection.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not row or row["customer"] != username:
            return JSONResponse(status_code=404, content=_response("ORDER_NOT_FOUND", message="订单不存在"))
        if row["status"] == "PAID":
            return JSONResponse(
                status_code=409,
                content=_response("ORDER_ALREADY_PAID", message="订单已支付"),
            )
        amount = payload.amount if payload.amount is not None else row["amount"]
        if amount != row["amount"]:
            return JSONResponse(
                status_code=400,
                content=_response("AMOUNT_MISMATCH", message="支付金额必须等于订单应付金额"),
            )
        fault_mode = os.getenv("DEMO_FAULT", "")
        if fault_mode != "payment_status":
            connection.execute(
                "UPDATE orders SET status='PAID', paid_amount=? WHERE id=?",
                (amount, order_id),
            )
            connection.commit()
        updated = connection.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    return _response("0000", _order_dict(updated), message="支付成功")


@app.post("/api/test/reset", include_in_schema=False)
def reset_test_data(request: Request) -> Dict[str, Any]:
    if os.getenv("APP_ENV", "local") != "local":
        raise HTTPException(status_code=404, detail="not found")
    reset_database()
    TOKENS.clear()
    return _response("0000", {"reset": True})
