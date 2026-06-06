from __future__ import annotations

import requests


CORE_BASE = "http://localhost:8001"


def quote(base_price: float) -> None:
    response = requests.post(f"{CORE_BASE}/price", json={"base_price": base_price}, timeout=5)
    response.raise_for_status()
    payload = response.json()

    print(f"Base price: {payload['base_price']}")
    for plugin in payload.get("plugins_applied", []):
        print(f"  - {plugin['plugin']}: {plugin['amount']}")
    print(f"Final price: {payload['final_price']}")
    print()


def main() -> None:
    print("=== Microkernel Microservices Demo Client ===")
    quote(100)
    quote(250)


if __name__ == "__main__":
    main()
