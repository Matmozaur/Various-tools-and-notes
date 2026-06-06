from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(title="Microkernel Tax Plugin Service")


class PriceRequest(BaseModel):
    base_price: float = Field(gt=0)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "plugin-tax-service"}


@app.post("/contribution")
def contribution(payload: PriceRequest) -> dict[str, str | float]:
    amount = round(payload.base_price * 0.10, 2)
    return {"plugin": "tax", "amount": amount}
