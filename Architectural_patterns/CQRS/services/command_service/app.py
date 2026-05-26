from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from redis import Redis


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
EVENT_STREAM = "events:accounts"

app = FastAPI(title="CQRS Command Service")
redis_client = Redis.from_url(REDIS_URL, decode_responses=True)


class CreateAccountRequest(BaseModel):
    owner: str = Field(min_length=1, max_length=100)


class DepositRequest(BaseModel):
    amount: float = Field(gt=0)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "command-service"}


@app.post("/accounts")
def create_account(payload: CreateAccountRequest) -> dict[str, str]:
    account_id = str(uuid4())
    key = f"write:account:{account_id}"

    # Write model state is stored independently from read model state.
    redis_client.hset(
        key,
        mapping={
            "owner": payload.owner,
            "balance": "0.0",
            "created_at": datetime.now(UTC).isoformat(),
        },
    )

    redis_client.xadd(
        EVENT_STREAM,
        {
            "event_type": "AccountCreated",
            "account_id": account_id,
            "owner": payload.owner,
            "occurred_at": datetime.now(UTC).isoformat(),
        },
    )

    return {"account_id": account_id}


@app.post("/accounts/{account_id}/deposit")
def deposit_money(account_id: UUID, payload: DepositRequest) -> dict[str, str]:
    key = f"write:account:{account_id}"
    data = redis_client.hgetall(key)
    if not data:
        raise HTTPException(status_code=404, detail="Account not found")

    current_balance = float(data.get("balance", "0.0"))
    new_balance = current_balance + payload.amount

    redis_client.hset(key, mapping={"balance": str(new_balance)})
    redis_client.xadd(
        EVENT_STREAM,
        {
            "event_type": "MoneyDeposited",
            "account_id": str(account_id),
            "amount": str(payload.amount),
            "occurred_at": datetime.now(UTC).isoformat(),
        },
    )

    return {"status": "accepted"}
