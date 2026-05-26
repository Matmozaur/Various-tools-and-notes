from __future__ import annotations

import os
import time
from datetime import UTC, datetime

from redis import Redis


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
EVENT_STREAM = "events:accounts"
PROJECTOR_DELAY_MS = int(os.getenv("PROJECTOR_DELAY_MS", "300"))


def append_ledger_entry(redis_client: Redis, account_id: str, entry: str) -> None:
    redis_client.rpush(f"read:ledger:{account_id}", entry)


def handle_account_created(redis_client: Redis, payload: dict[str, str]) -> None:
    account_id = payload["account_id"]
    owner = payload["owner"]
    occurred_at = payload["occurred_at"]

    redis_client.hset(
        f"read:account:{account_id}",
        mapping={"owner": owner, "balance": "0.0"},
    )
    append_ledger_entry(
        redis_client,
        account_id,
        f"[{occurred_at}] Account created for {owner}.",
    )


def handle_money_deposited(redis_client: Redis, payload: dict[str, str]) -> None:
    account_id = payload["account_id"]
    amount = float(payload["amount"])
    occurred_at = payload["occurred_at"]

    read_key = f"read:account:{account_id}"
    current_data = redis_client.hgetall(read_key)
    current_balance = float(current_data.get("balance", "0.0"))
    new_balance = current_balance + amount

    redis_client.hset(read_key, mapping={"balance": str(new_balance)})
    append_ledger_entry(
        redis_client,
        account_id,
        f"[{occurred_at}] Deposited ${amount:.2f}.",
    )


def project_forever() -> None:
    redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    last_stream_id = "0-0"

    print("[projector] started")

    while True:
        stream_response = redis_client.xread(
            {EVENT_STREAM: last_stream_id},
            block=5000,
            count=10,
        )

        if not stream_response:
            continue

        for _, events in stream_response:
            for stream_id, payload in events:
                event_type = payload.get("event_type")
                if event_type == "AccountCreated":
                    handle_account_created(redis_client, payload)
                elif event_type == "MoneyDeposited":
                    handle_money_deposited(redis_client, payload)
                else:
                    print(f"[projector] unknown event type: {event_type}")

                last_stream_id = stream_id
                time.sleep(PROJECTOR_DELAY_MS / 1000)


def main() -> None:
    print(f"[projector] boot at {datetime.now(UTC).isoformat()}")
    project_forever()


if __name__ == "__main__":
    main()
