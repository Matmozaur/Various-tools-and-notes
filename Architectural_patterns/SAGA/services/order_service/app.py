from __future__ import annotations

import os
import threading
from datetime import UTC, datetime
from uuid import uuid4

import psycopg
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from psycopg.rows import dict_row
from redis import Redis

from services.common.runtime import iter_events, publish_event, wait_for_postgres, wait_for_redis


POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://postgres:postgres@postgres:5432/orders_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://orchestrator-service:8001")

app = FastAPI(title="Saga Order Service")
redis_client: Redis | None = None


class CreateOrderRequest(BaseModel):
    customer: str = Field(min_length=1, max_length=100)
    sku: str = Field(min_length=1, max_length=100)
    amount: int = Field(gt=0)
    force_inventory_failure: bool = False


class InternalEventRequest(BaseModel):
    source: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=500)
    status: str | None = Field(default=None, max_length=30)


def get_connection() -> psycopg.Connection:
    return psycopg.connect(POSTGRES_DSN, autocommit=True, row_factory=dict_row)


def migrate() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    customer TEXT NOT NULL,
                    sku TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    flow_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS order_events (
                    event_id BIGSERIAL PRIMARY KEY,
                    order_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL
                )
                """
            )


def create_order(payload: CreateOrderRequest, flow_type: str) -> str:
    order_id = str(uuid4())
    now = datetime.now(UTC)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO orders (order_id, customer, sku, amount, flow_type, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (order_id, payload.customer, payload.sku, payload.amount, flow_type, "PENDING", now, now),
            )
            cursor.execute(
                """
                INSERT INTO order_events (order_id, source, message, created_at)
                VALUES (%s, %s, %s, %s)
                """,
                (order_id, "order-service", f"Created order via {flow_type} saga", now),
            )
    return order_id


def append_order_event(order_id: str, source: str, message: str, status: str | None = None) -> None:
    now = datetime.now(UTC)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            if status is not None:
                cursor.execute(
                    "UPDATE orders SET status = %s, updated_at = %s WHERE order_id = %s",
                    (status, now, order_id),
                )
            cursor.execute(
                """
                INSERT INTO order_events (order_id, source, message, created_at)
                VALUES (%s, %s, %s, %s)
                """,
                (order_id, source, message, now),
            )


def order_exists(order_id: str) -> bool:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM orders WHERE order_id = %s", (order_id,))
            return cursor.fetchone() is not None


def event_listener() -> None:
    assert redis_client is not None
    for event in iter_events(redis_client):
        if event.get("variant") != "choreography":
            continue

        order_id = event.get("order_id", "")
        if not order_id or not order_exists(order_id):
            continue

        event_type = event.get("type")
        if event_type == "PaymentReserved":
            append_order_event(order_id, "payment-service", "Payment reserved", status="IN_PROGRESS")
        elif event_type == "InventoryReserved":
            append_order_event(order_id, "inventory-service", "Inventory reserved", status="IN_PROGRESS")
        elif event_type == "ShipmentScheduled":
            append_order_event(order_id, "shipping-service", "Shipment scheduled", status="CONFIRMED")
        elif event_type == "InventoryFailed":
            reason = event.get("reason", "inventory unavailable")
            append_order_event(order_id, "inventory-service", f"Inventory failed: {reason}", status="REJECTED")
        elif event_type == "PaymentReleased":
            append_order_event(order_id, "payment-service", "Payment reservation released")


@app.on_event("startup")
def startup() -> None:
    global redis_client
    wait_for_postgres(POSTGRES_DSN)
    migrate()
    redis_client = wait_for_redis(REDIS_URL)
    threading.Thread(target=event_listener, daemon=True).start()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "order-service"}


@app.post("/orchestration/orders")
def create_orchestration_order(payload: CreateOrderRequest) -> dict[str, str]:
    order_id = create_order(payload, flow_type="orchestration")
    append_order_event(order_id, "order-service", "Forwarded order to saga orchestrator", status="IN_PROGRESS")

    response = requests.post(
        f"{ORCHESTRATOR_URL}/sagas/orders/{order_id}/execute",
        json={
            "order_id": order_id,
            "customer": payload.customer,
            "sku": payload.sku,
            "amount": payload.amount,
            "force_inventory_failure": payload.force_inventory_failure,
        },
        timeout=30,
    )
    if response.status_code >= 400:
        append_order_event(order_id, "order-service", "Failed to reach orchestrator", status="REJECTED")
        raise HTTPException(status_code=502, detail="Orchestrator unavailable")

    return {"order_id": order_id, "status": "accepted", "flow_type": "orchestration"}


@app.post("/choreography/orders")
def create_choreography_order(payload: CreateOrderRequest) -> dict[str, str]:
    if redis_client is None:
        raise HTTPException(status_code=503, detail="Redis not ready")

    order_id = create_order(payload, flow_type="choreography")
    append_order_event(order_id, "order-service", "Published OrderCreated event", status="IN_PROGRESS")
    publish_event(
        redis_client,
        {
            "type": "OrderCreated",
            "variant": "choreography",
            "order_id": order_id,
            "customer": payload.customer,
            "sku": payload.sku,
            "amount": payload.amount,
            "force_inventory_failure": payload.force_inventory_failure,
        },
    )
    return {"order_id": order_id, "status": "accepted", "flow_type": "choreography"}


@app.post("/internal/orders/{order_id}/events")
def add_internal_order_event(order_id: str, payload: InternalEventRequest) -> dict[str, str]:
    if not order_exists(order_id):
        raise HTTPException(status_code=404, detail="Order not found")
    append_order_event(order_id, payload.source, payload.message, payload.status)
    return {"status": "ok"}


@app.get("/orders/{order_id}")
def get_order(order_id: str) -> dict:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,))
            order = cursor.fetchone()
            if order is None:
                raise HTTPException(status_code=404, detail="Order not found")

            cursor.execute(
                """
                SELECT source, message, created_at
                FROM order_events
                WHERE order_id = %s
                ORDER BY event_id ASC
                """,
                (order_id,),
            )
            events = cursor.fetchall()

    return {
        "order_id": order["order_id"],
        "customer": order["customer"],
        "sku": order["sku"],
        "amount": order["amount"],
        "flow_type": order["flow_type"],
        "status": order["status"],
        "events": [
            {
                "source": event["source"],
                "message": event["message"],
                "created_at": event["created_at"].isoformat(),
            }
            for event in events
        ],
    }