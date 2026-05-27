from __future__ import annotations

import os
import threading
from datetime import UTC, datetime

import psycopg
from fastapi import FastAPI
from pydantic import BaseModel, Field
from redis import Redis

from services.common.runtime import iter_events, publish_event, wait_for_postgres, wait_for_redis


POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://postgres:postgres@postgres:5432/payments_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = FastAPI(title="Saga Payment Service")
redis_client: Redis | None = None


class ReservePaymentRequest(BaseModel):
    order_id: str = Field(min_length=1)
    amount: int = Field(gt=0)


def get_connection() -> psycopg.Connection:
    return psycopg.connect(POSTGRES_DSN, autocommit=True)


def migrate() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS payment_reservations (
                    order_id TEXT PRIMARY KEY,
                    amount INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )


def reserve_payment(order_id: str, amount: int) -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO payment_reservations (order_id, amount, status, updated_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (order_id)
                DO UPDATE SET amount = EXCLUDED.amount, status = EXCLUDED.status, updated_at = EXCLUDED.updated_at
                """,
                (order_id, amount, "RESERVED", datetime.now(UTC)),
            )


def release_payment(order_id: str) -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE payment_reservations
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

        event_type = event.get("type")
        order_id = event.get("order_id", "")
        if event_type == "OrderCreated":
            amount = int(event.get("amount", 0))
            sku = str(event.get("sku", ""))
            force_inventory_failure = bool(event.get("force_inventory_failure", False))
            reserve_payment(order_id, amount)
            publish_event(
                redis_client,
                {
                    "type": "PaymentReserved",
                    "variant": "choreography",
                    "order_id": order_id,
                    "amount": amount,
                    "sku": sku,
                    "force_inventory_failure": force_inventory_failure,
                },
            )
        elif event_type == "InventoryFailed":
            release_payment(order_id)
            publish_event(
                redis_client,
                {
                    "type": "PaymentReleased",
                    "variant": "choreography",
                    "order_id": order_id,
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
    return {"status": "ok", "service": "payment-service"}


@app.post("/payments/reservations")
def reserve(payload: ReservePaymentRequest) -> dict[str, str]:
    reserve_payment(payload.order_id, payload.amount)
    return {"status": "reserved"}


@app.post("/payments/reservations/{order_id}/release")
def release(order_id: str) -> dict[str, str]:
    release_payment(order_id)
    return {"status": "released"}