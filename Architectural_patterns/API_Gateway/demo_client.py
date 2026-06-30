from __future__ import annotations

import requests


GATEWAY_BASE = "http://localhost:8000"


def main() -> None:
    print("=== API Gateway Demo Client ===")

    alice = requests.post(
        f"{GATEWAY_BASE}/users",
        json={"name": "Alice", "email": "alice@example.com"},
        timeout=5,
    )
    alice.raise_for_status()
    user_id = alice.json()["id"]
    print(f"Created user: {alice.json()}")

    product = requests.post(
        f"{GATEWAY_BASE}/products",
        json={"name": "Widget", "price": 19.99},
        timeout=5,
    )
    product.raise_for_status()
    product_id = product.json()["id"]
    print(f"Created product: {product.json()}")

    order = requests.post(
        f"{GATEWAY_BASE}/orders",
        json={"user_id": user_id, "product_id": product_id, "quantity": 2},
        timeout=5,
    )
    order.raise_for_status()
    order_id = order.json()["id"]
    print(f"Created order: {order.json()}")

    users = requests.get(f"{GATEWAY_BASE}/users", timeout=5)
    users.raise_for_status()
    print(f"All users: {users.json()}")

    products = requests.get(f"{GATEWAY_BASE}/products", timeout=5)
    products.raise_for_status()
    print(f"All products: {products.json()}")

    orders = requests.get(f"{GATEWAY_BASE}/orders", timeout=5)
    orders.raise_for_status()
    print(f"All orders: {orders.json()}")

    summary = requests.get(f"{GATEWAY_BASE}/users/{user_id}/summary", timeout=5)
    summary.raise_for_status()
    print(f"User summary (aggregated): {summary.json()}")


if __name__ == "__main__":
    main()
