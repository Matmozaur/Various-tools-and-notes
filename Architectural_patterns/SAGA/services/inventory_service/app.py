from __future__ import annotations

import os
import threading
from datetime import UTC, datetime

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from redis import Redis

from services.common.runtime import iter_events, publish_event, wait_for_postgres, wait_for_redis


POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://postgres:postgres@postgres:5432/inventory_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = FastAPI(title="Saga Inventory Service")
redis_client: Redis | None = None


class ReserveInventoryRequest(BaseModel):
    order_id: str = Field(min_length=1)
    sku: str = Field(min_length=1, max_length=100)
    force_inventory_failure: bool = False


def get_connection() -> psycopg.Connection:
    return psycopg.connect(POSTGRES_DSN, autocommit=True)


def migrate() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS inventory_reservations (
                    order_id TEXT PRIMARY KEY,
                    sku TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )


def reserve_inventory(order_id: str, sku: str, force_inventory_failure: bool) -> None:
    if force_inventory_failure or sku == "sold-out":
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO inventory_reservations (order_id, sku, status, updated_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (order_id)
                    DO UPDATE SET sku = EXCLUDED.sku, status = EXCLUDED.status, updated_at = EXCLUDED.updated_at
                    """,
                    (order_id, sku, "REJECTED", datetime.now(UTC)),
                )
        raise HTTPException(status_code=409, detail="Inventory unavailable")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO inventory_reservations (order_id, sku, status, updated_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (order_id)
                DO UPDATE SET sku = EXCLUDED.sku, status = EXCLUDED.status, updated_at = EXCLUDED.updated_at
                """,
                (order_id, sku, "RESERVED", datetime.now(UTC)),
            )


def release_inventory(order_id: str) -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE inventory_reservations
                SET status = %s, updated_at = %s
                WHERE order_id = %s
                """,
                ("RELEASED", datetime.now(UTC), order_id),
            )


def choreography_listener() -> None:
    assert redis_client is not None
    for event in iter_events(redis_client):
        if event.get("variant") != "choreography":
            continue
        if event.get("type") != "PaymentReserved":
            continue

        order_id = event.get("order_id", "")
        sku = event.get("sku", "")
        should_fail = bool(event.get("force_inventory_failure", False))

        try:
            reserve_inventory(order_id, sku, should_fail)
            publish_event(
                redis_client,
                {
                    "type": "InventoryReserved",
                    "variant": "choreography",
                    "order_id": order_id,
                    "sku": sku,
                },
            )
        except HTTPException as error:
            publish_event(
                redis_client,
                {
                    "type": "InventoryFailed",
                    "variant": "choreography",
                    "order_id": order_id,
                    "reason": error.detail,
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
    return {"status": "ok", "service": "inventory-service"}


@app.post("/inventory/reservations")
def reserve(payload: ReserveInventoryRequest) -> dict[str, str]:
    reserve_inventory(payload.order_id, payload.sku, payload.force_inventory_failure)
    return {"status": "reserved"}


@app.post("/inventory/reservations/{order_id}/release")
def release(order_id: str) -> dict[str, str]:
    release_inventory(order_id)
    return {"status": "released"}