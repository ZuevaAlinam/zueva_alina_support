"""Замер времени ответа операций сервиса.

Запуск:
    python -m tests.bench
"""
import statistics
import time
from typing import Callable, List

import httpx

BASE_URL = "http://localhost:8000"
USERNAME = "user0"
PASSWORD = "demo"
REPEATS = 25
WARMUP = 5


def login(client: httpx.Client) -> None:
    r = client.post(f"{BASE_URL}/api/auth/login",
                    json={"username": USERNAME, "password": PASSWORD})
    r.raise_for_status()


def measure(name: str, func: Callable[[], httpx.Response]) -> dict:
    for _ in range(WARMUP):
        func()
    times: List[float] = []
    status = None
    for _ in range(REPEATS):
        t0 = time.perf_counter()
        r = func()
        dt = (time.perf_counter() - t0) * 1000
        times.append(dt)
        status = r.status_code
    times.sort()
    p50 = statistics.median(times)
    p95 = times[int(len(times) * 0.95) - 1]
    return {
        "operation": name,
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "max_ms": round(max(times), 2),
        "min_ms": round(min(times), 2),
        "status": status,
    }


def main():
    with httpx.Client(timeout=120.0) as client:
        login(client)

        # Определяем реальные id из базы
        r = client.get(f"{BASE_URL}/api/tickets", params={"page": 1, "size": 1})
        r.raise_for_status()
        first_ticket_id = r.json()["items"][0]["id"]
        first_category_id = r.json()["items"][0]["category_id"]
        print(f"Используем ticket_id={first_ticket_id}, category_id={first_category_id}")

        results = [
            measure("GET /api/tickets (page 1)",
                    lambda: client.get(f"{BASE_URL}/api/tickets",
                                       params={"page": 1, "size": 20})),
            measure("GET /api/tickets (page 500)",
                    lambda: client.get(f"{BASE_URL}/api/tickets",
                                       params={"page": 500, "size": 20})),
            measure(f"GET /api/tickets/{first_ticket_id}",
                    lambda: client.get(f"{BASE_URL}/api/tickets/{first_ticket_id}")),
            measure("POST /api/tickets",
                    lambda: client.post(f"{BASE_URL}/api/tickets",
                                        json={"title": "Bench",
                                              "body": "Test ticket from bench",
                                              "category_id": first_category_id})),
            measure("GET /api/summary",
                    lambda: client.get(f"{BASE_URL}/api/summary")),
        ]

    print(f"\n{'Operation':<35} {'p50':>8} {'p95':>8} {'max':>8} {'status':>6}")
    print("-" * 75)
    for r in results:
        print(f"{r['operation']:<35} {r['p50_ms']:>8} {r['p95_ms']:>8} "
              f"{r['max_ms']:>8} {r['status']:>6}")


if __name__ == "__main__":
    main()