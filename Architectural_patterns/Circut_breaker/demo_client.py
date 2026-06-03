from __future__ import annotations

import time

import requests


GATEWAY_BASE = "http://localhost:8001"
DOWNSTREAM_BASE = "http://localhost:8002"


def show_call(step: str, response: requests.Response) -> None:
    try:
        payload = response.json()
    except ValueError:
        payload = {"raw": response.text}
    print(f"{step}: status={response.status_code}, body={payload}")


def main() -> None:
    print("=== Circuit Breaker Demo Client ===")

    control = requests.post(f"{DOWNSTREAM_BASE}/control", json={"mode": "healthy", "slow_seconds": 2.5}, timeout=5)
    control.raise_for_status()
    print("Downstream set to healthy")

    first = requests.get(f"{GATEWAY_BASE}/proxy", timeout=5)
    show_call("Healthy call", first)

    control = requests.post(f"{DOWNSTREAM_BASE}/control", json={"mode": "fail", "slow_seconds": 2.5}, timeout=5)
    control.raise_for_status()
    print("Downstream set to fail")

    for attempt in range(1, 5):
        resp = requests.get(f"{GATEWAY_BASE}/proxy", timeout=5)
        show_call(f"Failure attempt {attempt}", resp)

    breaker_open = requests.get(f"{GATEWAY_BASE}/breaker", timeout=5)
    show_call("Breaker after failures", breaker_open)

    control = requests.post(f"{DOWNSTREAM_BASE}/control", json={"mode": "healthy", "slow_seconds": 2.5}, timeout=5)
    control.raise_for_status()
    print("Downstream switched back to healthy")

    blocked = requests.get(f"{GATEWAY_BASE}/proxy", timeout=5)
    show_call("Call while open", blocked)

    print("Waiting for recovery timeout...")
    time.sleep(6)

    recovered = requests.get(f"{GATEWAY_BASE}/proxy", timeout=5)
    show_call("Half-open probe call", recovered)

    breaker_closed = requests.get(f"{GATEWAY_BASE}/breaker", timeout=5)
    show_call("Breaker after recovery", breaker_closed)


if __name__ == "__main__":
    main()
