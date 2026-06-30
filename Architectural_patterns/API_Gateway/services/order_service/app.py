from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


SERVICE_NAME = os.getenv("SERVICE_NAME", "order-service")

app = FastAPI(title="Order Service")
orders: dict[str, dict[str, str | float]] = {}


class CreateOrderRequest(BaseModel):
    user_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    quantity: int = Field(gt=0)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME}


@app.get("/orders")
def list_orders() -> dict[str, object]:
    return {"orders": [{"id": oid, **o} for oid, o in orders.items()]}


@app.post("/orders")
def create_order(payload: CreateOrderRequest) -> dict[str, str | float]:
    order_id = str(uuid4())
    orders[order_id] = {
        "user_id": payload.user_id,
        "product_id": payload.product_id,
        "quantity": payload.quantity,
        "status": "created",
        "created_at": datetime.now(UTC).isoformat(),
    }
    return {"id": order_id, **orders[order_id]}


@app.get("/orders/{order_id}")
def get_order(order_id: str) -> dict[str, str | float]:
    order = orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"id": order_id, **order}


@app.get("/users/{user_id}/orders")
def get_user_orders(user_id: str) -> dict[str, object]:
    user_orders = [
        {"id": oid, **o} for oid, o in orders.items() if o.get("user_id") == user_id
    ]
    return {"user_id": user_id, "orders": user_orders}
