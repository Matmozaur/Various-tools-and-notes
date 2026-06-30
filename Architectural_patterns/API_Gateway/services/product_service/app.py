from __future__ import annotations

import os
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


SERVICE_NAME = os.getenv("SERVICE_NAME", "product-service")

app = FastAPI(title="Product Service")
products: dict[str, dict[str, str | float]] = {}


class CreateProductRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME}


@app.get("/products")
def list_products() -> dict[str, object]:
    return {"products": [{"id": pid, **p} for pid, p in products.items()]}


@app.post("/products")
def create_product(payload: CreateProductRequest) -> dict[str, str | float]:
    product_id = str(uuid4())
    products[product_id] = {"name": payload.name, "price": payload.price}
    return {"id": product_id, "name": payload.name, "price": payload.price}


@app.get("/products/{product_id}")
def get_product(product_id: str) -> dict[str, str | float]:
    product = products.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"id": product_id, **product}
