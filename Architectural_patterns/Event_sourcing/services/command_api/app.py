import json
import os
from fastapi import FastAPI
from pydantic import BaseModel
from kafka import KafkaProducer

app = FastAPI()

KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "localhost:9092")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "account-events")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)


class OpenAccountIn(BaseModel):
    account_id: str
    owner: str


class AmountIn(BaseModel):
    amount: int


def publish(event: dict) -> None:
    producer.send(KAFKA_TOPIC, event)
    producer.flush()


@app.post("/accounts")
def open_account(payload: OpenAccountIn) -> dict:
    publish({
        "type": "AccountOpened",
        "account_id": payload.account_id,
        "owner": payload.owner,
    })
    return {"status": "ok"}


@app.post("/accounts/{account_id}/deposit")
def deposit(account_id: str, payload: AmountIn) -> dict:
    publish({
        "type": "MoneyDeposited",
        "account_id": account_id,
        "amount": payload.amount,
    })
    return {"status": "ok"}


@app.post("/accounts/{account_id}/withdraw")
def withdraw(account_id: str, payload: AmountIn) -> dict:
    publish({
        "type": "MoneyWithdrawn",
        "account_id": account_id,
        "amount": payload.amount,
    })
    return {"status": "ok"}
