import json
import os
import time
from kafka import KafkaConsumer
import psycopg2

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
                CREATE TABLE IF NOT EXISTS account_balances (
                    account_id TEXT PRIMARY KEY,
                    owner TEXT NOT NULL,
                    balance INT NOT NULL
                )
                """
            )


def apply_event(conn: psycopg2.extensions.connection, event: dict) -> None:
    event_type = event.get("type")
    account_id = event.get("account_id")

    with conn:
        with conn.cursor() as cur:
            if event_type == "AccountOpened":
                cur.execute(
                    """
                    INSERT INTO account_balances (account_id, owner, balance)
                    VALUES (%s, %s, 0)
                    ON CONFLICT (account_id)
                    DO UPDATE SET owner = EXCLUDED.owner, balance = EXCLUDED.balance
                    """,
                    (account_id, event.get("owner", "")),
                )
            elif event_type == "MoneyDeposited":
                amount = int(event.get("amount", 0))
                cur.execute(
                    "UPDATE account_balances SET balance = balance + %s WHERE account_id = %s",
                    (amount, account_id),
                )
                if cur.rowcount == 0:
                    cur.execute(
                        "INSERT INTO account_balances (account_id, owner, balance) VALUES (%s, %s, %s)",
                        (account_id, "", amount),
                    )
            elif event_type == "MoneyWithdrawn":
                amount = int(event.get("amount", 0))
                cur.execute(
                    "UPDATE account_balances SET balance = balance - %s WHERE account_id = %s",
                    (amount, account_id),
                )
                if cur.rowcount == 0:
                    cur.execute(
                        "INSERT INTO account_balances (account_id, owner, balance) VALUES (%s, %s, %s)",
                        (account_id, "", -amount),
                    )


def main() -> None:
    conn = connect_postgres()
    ensure_tables(conn)

    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        group_id="projection",
        enable_auto_commit=True,
    )

    for msg in consumer:
        apply_event(conn, msg.value)


if __name__ == "__main__":
    main()
