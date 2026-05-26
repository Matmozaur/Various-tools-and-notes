from __future__ import annotations

import time

import requests


COMMAND_BASE = "http://localhost:8001"
QUERY_BASE = "http://localhost:8002"


def main() -> None:
    print("=== CQRS Microservices Demo Client ===")

    create_resp = requests.post(f"{COMMAND_BASE}/accounts", json={"owner": "Alice"}, timeout=5)
    create_resp.raise_for_status()
    account_id = create_resp.json()["account_id"]
    print(f"Created account: {account_id}")

    deposit_resp = requests.post(
        f"{COMMAND_BASE}/accounts/{account_id}/deposit",
        json={"amount": 150.0},
        timeout=5,
    )
    deposit_resp.raise_for_status()
    print("Deposit command accepted")

    stale_balance = requests.get(f"{QUERY_BASE}/accounts/{account_id}/balance", timeout=5)
    stale_balance.raise_for_status()
    print(f"Balance immediately after command: {stale_balance.json()['balance']}")

    time.sleep(1.2)

    fresh_balance = requests.get(f"{QUERY_BASE}/accounts/{account_id}/balance", timeout=5)
    fresh_balance.raise_for_status()
    print(f"Balance after projector catch-up: {fresh_balance.json()['balance']}")

    ledger = requests.get(f"{QUERY_BASE}/accounts/{account_id}/ledger", timeout=5)
    ledger.raise_for_status()
    print("Ledger entries:")
    for line in ledger.json().get("entries", []):
        print(f"  - {line}")


if __name__ == "__main__":
    main()
