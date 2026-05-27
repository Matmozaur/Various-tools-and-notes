from __future__ import annotations

import os
import threading
from datetime import UTC, datetime

import psycopg
from fastapi import FastAPI
from pydantic import BaseModel, Field
from redis import Redis

from services.common.runtime import iter_events, publish_event, wait_for_postgres, wait_for_redis


POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://postgres:postgres@postgres:5432/shipping_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = FastAPI(title="Saga Shipping Service")
redis_client: Redis | None = None


class ScheduleShipmentRequest(BaseModel):
    order_id: str = Field(min_length=1)
    sku: str = Field(min_length=1, max_length=100)


def get_connection() -> psycopg.Connection:
    return psycopg.connect(POSTGRES_DSN, autocommit=True)


def migrate() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS shipments (
                    order_id TEXT PRIMARY KEY,
                    sku TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )


def schedule_shipment(order_id: str, sku: str) -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO shipments (order_id, sku, status, updated_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (order_id)
                DO UPDATE SET sku = EXCLUDED.sku, status = EXCLUDED.status, updated_at = EXCLUDED.updated_at
                """,
                (order_id, sku, "SCHEDULED", datetime.now(UTC)),
            )


def cancel_shipment(order_id: str) -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE shipments
                SET status = %s, updated_at = %s
                WHERE order_id = %s
                """,
                ("CANCELED", datetime.now(UTC), order_id),
            )


def choreography_listener() -> None:
    assert redis_client is not None
    for event in iter_events(redis_client):
        if event.get("variant") != "choreography":
            continue
        if event.get("type") != "InventoryReserved":
            continue

        order_id = event.get("order_id", "")
        sku = event.get("sku", "")
        schedule_shipment(order_id, sku)
        publish_event(
            redis_client,
            {
                "type": "ShipmentScheduled",
                "variant": "choreography",
                "order_id": order_id,
                "sku": sku,
            },
        )


@app.on_event("startup")
def startup() -> None:
    global redis_client
    wait_for_postgres(POSTGRES_DSN)
    migrate()
    redis_client = wait_for_redis(REDIS_URL)
    threading.Thread(target=choreography_listener, daemon=True).start()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "shipping-service"}


@app.post("/shipments")
def schedule(payload: ScheduleShipmentRequest) -> dict[str, str]:
    schedule_shipment(payload.order_id, payload.sku)
    return {"status": "scheduled"}


@app.post("/shipments/{order_id}/cancel")
def cancel(order_id: str) -> dict[str, str]:
    cancel_shipment(order_id)
    return {"status": "canceled"}