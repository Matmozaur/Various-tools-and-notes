from __future__ import annotations

import json
import time
from typing import Any, Iterator

import psycopg
from redis import Redis


EVENT_CHANNEL = "saga-events"


def wait_for_postgres(dsn: str, attempts: int = 30, delay: float = 1.0) -> None:
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            with psycopg.connect(dsn, autocommit=True) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
            return
        except Exception as error:  # pragma: no cover - startup retry path
            last_error = error
            time.sleep(delay)
    raise RuntimeError(f"Postgres not ready: {last_error}")


def wait_for_redis(url: str, attempts: int = 30, delay: float = 1.0) -> Redis:
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            client = Redis.from_url(url, decode_responses=True)
            client.ping()
            return client
        except Exception as error:  # pragma: no cover - startup retry path
            last_error = error
            time.sleep(delay)
    raise RuntimeError(f"Redis not ready: {last_error}")


def publish_event(redis_client: Redis, event: dict[str, Any]) -> None:
    redis_client.publish(EVENT_CHANNEL, json.dumps(event))


def iter_events(redis_client: Redis) -> Iterator[dict[str, Any]]:
    pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(EVENT_CHANNEL)
    for message in pubsub.listen():
        data = message.get("data")
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        if isinstance(data, str):
            yield json.loads(data)