import json
import os
import time
from kafka import KafkaConsumer
import psycopg2
from psycopg2.extras import Json

KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "localhost:9092")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "account-events")
POSTGRES_DSN = os.environ.get("POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/events")


def connect_postgres() -> psycopg2.extensions.connection:
    while True:
        try:
            return psycopg2.connect(POSTGRES_DSN)
        except psycopg2.OperationalError:
            time.sleep(1)


def ensure_tables(conn: psycopg2.extensions.connection) -> None:
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    data JSONB NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
                """
            )


def main() -> None:
    conn = connect_postgres()
    ensure_tables(conn)

    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        group_id="event-store",
        enable_auto_commit=True,
    )

    for msg in consumer:
        event = msg.value
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO events (account_id, type, data) VALUES (%s, %s, %s)",
                    (event.get("account_id"), event.get("type"), Json(event)),
                )


if __name__ == "__main__":
    main()
