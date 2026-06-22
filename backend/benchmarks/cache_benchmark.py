"""
Cache performance benchmark.

Measures response times with and without Redis caching on key API endpoints.
Requires a running PostgreSQL database and Redis server.

Usage:
    cd backend
    python -m benchmarks.cache_benchmark
"""

import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.redis_cache import cache


ENDPOINTS = [
    ("/api/games/recent?limit=10", "games:*"),
    ("/api/games/recent?limit=5&team=SJS", "games:*"),
]

N_REQUESTS = 50
WARMUP_REQUESTS = 3


def measure(client: TestClient, url: str, n: int) -> list[float]:
    times_ms = []
    for _ in range(n):
        start = time.perf_counter()
        resp = client.get(url)
        elapsed = (time.perf_counter() - start) * 1000
        if resp.status_code == 200:
            times_ms.append(elapsed)
    return times_ms


def run_benchmark():
    client = TestClient(app)

    # Discover a real game_id from the recent games list
    resp = client.get("/api/games/recent?limit=1")
    if resp.status_code == 200 and resp.json():
        game_id = resp.json()[0]["game_id"]
        ENDPOINTS.append((f"/api/games/{game_id}", f"game:{game_id}"))

    results = []

    for url, invalidation_pattern in ENDPOINTS:
        # --- Cold (no cache) ---
        cache.invalidate_pattern(invalidation_pattern)
        measure(client, url, WARMUP_REQUESTS)  # warmup JIT / connections

        cache.invalidate_pattern(invalidation_pattern)
        cold_times = []
        for _ in range(N_REQUESTS):
            cache.invalidate_pattern(invalidation_pattern)
            t = measure(client, url, 1)
            cold_times.extend(t)

        # --- Warm (cached) ---
        client.get(url)  # prime the cache
        measure(client, url, WARMUP_REQUESTS)  # warmup
        warm_times = measure(client, url, N_REQUESTS)

        if not cold_times or not warm_times:
            print(f"SKIP {url} — not enough successful responses")
            continue

        cold_mean = statistics.mean(cold_times)
        warm_mean = statistics.mean(warm_times)
        improvement = (cold_mean - warm_mean) / cold_mean * 100

        results.append({
            "endpoint": url,
            "cold_mean": cold_mean,
            "cold_p50": statistics.median(cold_times),
            "cold_p95": sorted(cold_times)[int(len(cold_times) * 0.95)],
            "warm_mean": warm_mean,
            "warm_p50": statistics.median(warm_times),
            "warm_p95": sorted(warm_times)[int(len(warm_times) * 0.95)],
            "improvement_pct": improvement,
        })

        print(f"{url}: cold={cold_mean:.1f}ms  warm={warm_mean:.1f}ms  improvement={improvement:.0f}%")

    write_report(results)


def write_report(results: list[dict]):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Cache Benchmark Results",
        "",
        f"_Generated {now} — N={N_REQUESTS} requests per measurement_",
        "",
        "| Endpoint | Cold mean (ms) | Cold p95 (ms) | Warm mean (ms) | Warm p95 (ms) | Improvement |",
        "|---|---|---|---|---|---|",
    ]

    for r in results:
        lines.append(
            f"| `{r['endpoint']}` "
            f"| {r['cold_mean']:.1f} "
            f"| {r['cold_p95']:.1f} "
            f"| {r['warm_mean']:.1f} "
            f"| {r['warm_p95']:.1f} "
            f"| **{r['improvement_pct']:.0f}%** |"
        )

    if results:
        avg_improvement = statistics.mean(r["improvement_pct"] for r in results)
        avg_warm_p95 = statistics.mean(r["warm_p95"] for r in results)
        lines.extend([
            "",
            f"**Average improvement: {avg_improvement:.0f}%**",
            f"**Average warm p95: {avg_warm_p95:.1f}ms**",
        ])

    lines.append("")

    out = Path(__file__).parent / "results.md"
    out.write_text("\n".join(lines))
    print(f"\nReport written to {out}")


if __name__ == "__main__":
    run_benchmark()
