from __future__ import annotations

import time

import requests


BASE_URL = "http://localhost:8000"


def create_orchestration_order(force_inventory_failure: bool) -> str:
    response = requests.post(
        f"{BASE_URL}/orchestration/orders",
        json={
            "customer": "Ada",
            "sku": "demo-item",
            "amount": 120,
            "force_inventory_failure": force_inventory_failure,
        },
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    return payload["order_id"]


def create_choreography_order(force_inventory_failure: bool) -> str:
    response = requests.post(
        f"{BASE_URL}/choreography/orders",
        json={
            "customer": "Grace",
            "sku": "demo-item",
            "amount": 75,
            "force_inventory_failure": force_inventory_failure,
        },
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    return payload["order_id"]


def wait_for_terminal_state(order_id: str) -> dict:
    for _ in range(20):
        response = requests.get(f"{BASE_URL}/orders/{order_id}", timeout=10)
        response.raise_for_status()
        payload = response.json()
        if payload["status"] in {"CONFIRMED", "REJECTED"}:
            return payload
        time.sleep(0.5)
    raise TimeoutError(f"Order {order_id} did not reach terminal state")


def print_order(title: str, order_id: str) -> None:
    payload = wait_for_terminal_state(order_id)
    print(title)
    print(f"  id: {payload['order_id']}")
    print(f"  flow: {payload['flow_type']}")
    print(f"  status: {payload['status']}")
    print("  timeline:")
    for entry in payload.get("events", []):
        print(f"    - [{entry['source']}] {entry['message']}")
    print()


def main() -> None:
    print("=== SAGA Microservices Demo Client ===")

    orchestration_ok = create_orchestration_order(force_inventory_failure=False)
    print_order("Orchestration success", orchestration_ok)

    orchestration_fail = create_orchestration_order(force_inventory_failure=True)
    print_order("Orchestration compensation", orchestration_fail)

    choreography_ok = create_choreography_order(force_inventory_failure=False)
    print_order("Choreography success", choreography_ok)

    choreography_fail = create_choreography_order(force_inventory_failure=True)
    print_order("Choreography compensation", choreography_fail)


if __name__ == "__main__":
    main()