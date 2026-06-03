from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Literal

import requests
from fastapi import FastAPI, HTTPException


SERVICE_NAME = os.getenv("SERVICE_NAME", "gateway-service")
DOWNSTREAM_URL = os.getenv("DOWNSTREAM_URL", "http://downstream-service:8002/work")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "1.5"))
FAILURE_THRESHOLD = int(os.getenv("FAILURE_THRESHOLD", "3"))
RECOVERY_TIMEOUT_SECONDS = int(os.getenv("RECOVERY_TIMEOUT_SECONDS", "5"))

CircuitState = Literal["closed", "open", "half_open"]


@dataclass
class CircuitBreaker:
    failure_threshold: int
    recovery_timeout_seconds: int
    state: CircuitState = "closed"
    consecutive_failures: int = 0
    opened_at: datetime | None = None
    lock: Lock = field(default_factory=Lock)

    def allow_request(self) -> bool:
        with self.lock:
            if self.state == "closed":
                return True

            if self.state == "open":
                if self.opened_at is None:
                    return False

                recovery_time = self.opened_at + timedelta(seconds=self.recovery_timeout_seconds)
                if datetime.now(UTC) >= recovery_time:
                    self.state = "half_open"
                    return True

                return False

            return self.state == "half_open"

    def on_success(self) -> None:
        with self.lock:
            self.state = "closed"
            self.consecutive_failures = 0
            self.opened_at = None

    def on_failure(self) -> None:
        with self.lock:
            self.consecutive_failures += 1

            if self.state == "half_open" or self.consecutive_failures >= self.failure_threshold:
                self.state = "open"
                self.opened_at = datetime.now(UTC)


app = FastAPI(title="Circuit Breaker Gateway Service")
breaker = CircuitBreaker(
    failure_threshold=FAILURE_THRESHOLD,
    recovery_timeout_seconds=RECOVERY_TIMEOUT_SECONDS,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME}


@app.get("/breaker")
def breaker_state() -> dict[str, str | int | None]:
    opened_at = breaker.opened_at.isoformat() if breaker.opened_at else None
    return {
        "state": breaker.state,
        "consecutive_failures": breaker.consecutive_failures,
        "failure_threshold": breaker.failure_threshold,
        "recovery_timeout_seconds": breaker.recovery_timeout_seconds,
        "opened_at": opened_at,
    }


@app.get("/proxy")
def proxy() -> dict[str, object]:
    if not breaker.allow_request():
        raise HTTPException(status_code=503, detail="Circuit is open. Call denied.")

    try:
        response = requests.get(DOWNSTREAM_URL, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        breaker.on_failure()
        raise HTTPException(status_code=502, detail=f"Downstream error: {exc}") from exc

    breaker.on_success()
    return {
        "service": SERVICE_NAME,
        "circuit_state": breaker.state,
        "downstream": response.json(),
    }
