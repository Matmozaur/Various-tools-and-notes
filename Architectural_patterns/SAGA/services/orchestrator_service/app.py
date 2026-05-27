from __future__ import annotations

import os

import requests
from fastapi import FastAPI
from pydantic import BaseModel, Field


ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8000")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8002")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://inventory-service:8003")
SHIPPING_SERVICE_URL = os.getenv("SHIPPING_SERVICE_URL", "http://shipping-service:8004")

app = FastAPI(title="Saga Orchestrator Service")


class ExecuteSagaRequest(BaseModel):
    order_id: str = Field(min_length=1)
    customer: str = Field(min_length=1, max_length=100)
    sku: str = Field(min_length=1, max_length=100)
    amount: int = Field(gt=0)
    force_inventory_failure: bool = False


def record(order_id: str, source: str, message: str, status: str | None = None) -> None:
    response = requests.post(
        f"{ORDER_SERVICE_URL}/internal/orders/{order_id}/events",
        json={"source": source, "message": message, "status": status},
        timeout=10,
    )
    response.raise_for_status()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "orchestrator-service"}


@app.post("/sagas/orders/{order_id}/execute")
def execute(order_id: str, payload: ExecuteSagaRequest) -> dict[str, str]:
    payment_reserved = False
    inventory_reserved = False

    try:
        record(order_id, "orchestrator-service", "Starting orchestration saga", status="IN_PROGRESS")

        response = requests.post(
            f"{PAYMENT_SERVICE_URL}/payments/reservations",
            json={"order_id": order_id, "amount": payload.amount},
            timeout=10,
        )
        response.raise_for_status()
        payment_reserved = True
        record(order_id, "payment-service", "Payment reserved")

        response = requests.post(
            f"{INVENTORY_SERVICE_URL}/inventory/reservations",
            json={
                "order_id": order_id,
                "sku": payload.sku,
                "force_inventory_failure": payload.force_inventory_failure,
            },
            timeout=10,
        )
        response.raise_for_status()
        inventory_reserved = True
        record(order_id, "inventory-service", "Inventory reserved")

        response = requests.post(
            f"{SHIPPING_SERVICE_URL}/shipments",
            json={"order_id": order_id, "sku": payload.sku},
            timeout=10,
        )
        response.raise_for_status()
        record(order_id, "shipping-service", "Shipment scheduled", status="CONFIRMED")
        return {"status": "confirmed"}
    except requests.HTTPError as error:
        detail = error.response.text if error.response is not None else str(error)
        record(order_id, "orchestrator-service", f"Failure detected: {detail}")

        if inventory_reserved:
            requests.post(
                f"{INVENTORY_SERVICE_URL}/inventory/reservations/{order_id}/release",
                timeout=10,
            ).raise_for_status()
            record(order_id, "inventory-service", "Inventory reservation released")

        if payment_reserved:
            requests.post(
                f"{PAYMENT_SERVICE_URL}/payments/reservations/{order_id}/release",
                timeout=10,
            ).raise_for_status()
            record(order_id, "payment-service", "Payment reservation released")

        record(order_id, "orchestrator-service", "Order rejected after compensation", status="REJECTED")
        return {"status": "rejected"}