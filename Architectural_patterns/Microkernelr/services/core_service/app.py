from __future__ import annotations

import os
from dataclasses import dataclass

import requests
from fastapi import FastAPI
from pydantic import BaseModel, Field


PLUGIN_TIMEOUT_SECONDS = 3
RAW_PLUGIN_URLS = os.getenv("PLUGIN_URLS", "")
PLUGIN_URLS = [url.strip() for url in RAW_PLUGIN_URLS.split(",") if url.strip()]

app = FastAPI(title="Microkernel Core Service")


class PriceRequest(BaseModel):
    base_price: float = Field(gt=0)


@dataclass(slots=True)
class PluginResult:
    plugin: str
    amount: float


def call_plugin(plugin_base_url: str, base_price: float) -> PluginResult | None:
    endpoint = f"{plugin_base_url}/contribution"

    try:
        response = requests.post(endpoint, json={"base_price": base_price}, timeout=PLUGIN_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException:
        return None

    plugin_name = str(payload.get("plugin", "unknown"))
    amount = float(payload.get("amount", 0.0))
    return PluginResult(plugin=plugin_name, amount=amount)


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "core-service",
        "plugins_configured": PLUGIN_URLS,
    }


@app.post("/price")
def calculate_price(payload: PriceRequest) -> dict[str, object]:
    base_price = payload.base_price
    applied: list[dict[str, float | str]] = []
    total = base_price

    for plugin_url in PLUGIN_URLS:
        plugin_result = call_plugin(plugin_url, base_price)
        if plugin_result is None:
            continue

        total += plugin_result.amount
        applied.append({"plugin": plugin_result.plugin, "amount": plugin_result.amount})

    return {
        "base_price": base_price,
        "plugins_applied": applied,
        "final_price": round(total, 2),
    }
