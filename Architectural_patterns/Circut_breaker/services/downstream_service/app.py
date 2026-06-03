from __future__ import annotations

import os
import time
from datetime import UTC, datetime
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


SERVICE_NAME = os.getenv("SERVICE_NAME", "downstream-service")

app = FastAPI(title="Circuit Breaker Downstream Service")

state: dict[str, str | float] = {"mode": "healthy", "slow_seconds": 2.5}


class ControlRequest(BaseModel):
    mode: Literal["healthy", "fail", "slow"]
    slow_seconds: float = Field(default=2.5, ge=0.1, le=10.0)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME}


@app.post("/control")
def control(payload: ControlRequest) -> dict[str, str | float]:
    state["mode"] = payload.mode
    state["slow_seconds"] = payload.slow_seconds
    return {"mode": state["mode"], "slow_seconds": state["slow_seconds"]}


@app.get("/work")
def work() -> dict[str, str]:
    mode = str(state["mode"])
    if mode == "fail":
        raise HTTPException(status_code=503, detail="Downstream forced failure")

    if mode == "slow":
        time.sleep(float(state["slow_seconds"]))

    return {
        "service": SERVICE_NAME,
        "mode": mode,
        "message": "Downstream work completed",
        "timestamp": datetime.now(UTC).isoformat(),
    }
