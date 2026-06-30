from __future__ import annotations

import os

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


SERVICE_NAME = os.getenv("SERVICE_NAME", "gateway-service")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8001")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8002")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8003")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "5.0"))

app = FastAPI(title="API Gateway Service")


class CreateUserRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=1, max_length=200)


class CreateOrderRequest(BaseModel):
    user_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    quantity: int = Field(gt=0)


class CreateProductRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME}


def _forward_get(path: str, base_url: str) -> dict[str, object]:
    try:
        resp = requests.get(f"{base_url}{path}", timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def _forward_post(path: str, base_url: str, body: dict[str, object]) -> dict[str, object]:
    try:
        resp = requests.post(f"{base_url}{path}", json=body, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/users")
def list_users() -> dict[str, object]:
    return _forward_get("/users", USER_SERVICE_URL)


@app.post("/users")
def create_user(payload: CreateUserRequest) -> dict[str, object]:
    return _forward_post("/users", USER_SERVICE_URL, payload.model_dump())


@app.get("/users/{user_id}")
def get_user(user_id: str) -> dict[str, object]:
    return _forward_get(f"/users/{user_id}", USER_SERVICE_URL)


@app.get("/products")
def list_products() -> dict[str, object]:
    return _forward_get("/products", PRODUCT_SERVICE_URL)


@app.post("/products")
def create_product(payload: CreateProductRequest) -> dict[str, object]:
    return _forward_post("/products", PRODUCT_SERVICE_URL, payload.model_dump())


@app.get("/orders")
def list_orders() -> dict[str, object]:
    return _forward_get("/orders", ORDER_SERVICE_URL)


@app.post("/orders")
def create_order(payload: CreateOrderRequest) -> dict[str, object]:
    return _forward_post("/orders", ORDER_SERVICE_URL, payload.model_dump())


@app.get("/orders/{order_id}")
def get_order(order_id: str) -> dict[str, object]:
    return _forward_get(f"/orders/{order_id}", ORDER_SERVICE_URL)


@app.get("/users/{user_id}/summary")
def user_summary(user_id: str) -> dict[str, object]:
    user = _forward_get(f"/users/{user_id}", USER_SERVICE_URL)
    orders = _forward_get(f"/users/{user_id}/orders", ORDER_SERVICE_URL)
    return {"user": user, "orders": orders}
