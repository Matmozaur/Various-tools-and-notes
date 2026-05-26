from __future__ import annotations

import os
from uuid import UUID

from fastapi import FastAPI
from redis import Redis


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = FastAPI(title="CQRS Query Service")
redis_client = Redis.from_url(REDIS_URL, decode_responses=True)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "query-service"}


@app.get("/accounts/{account_id}/balance")
def get_balance(account_id: UUID) -> dict[str, str | float]:
    key = f"read:account:{account_id}"
    data = redis_client.hgetall(key)
    if not data:
        return {"account_id": str(account_id), "owner": "unknown", "balance": 0.0}

    return {
        "account_id": str(account_id),
        "owner": data.get("owner", "unknown"),
        "balance": float(data.get("balance", "0.0")),
    }


@app.get("/accounts/{account_id}/ledger")
def get_ledger(account_id: UUID) -> dict[str, object]:
    ledger_key = f"read:ledger:{account_id}"
    events = redis_client.lrange(ledger_key, 0, -1)
    return {"account_id": str(account_id), "entries": events}
