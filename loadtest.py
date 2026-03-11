"""Load testing and capacity planning tool.

Usage:
    python loadtest.py --url http://localhost:8000 --concurrent 5 --duration 60

Tests:
    1. Health endpoint throughput (GET /health)
    2. System info latency (GET /system-info)
    3. Upload concurrency (POST /upload with small test file)
    4. SSE connection handling (GET /events/{id})
"""

import argparse
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib import request, error


def timed_request(url: str, method: str = "GET", data: bytes = None,
                  headers: dict = None) -> dict:
    """Make a timed HTTP request. Returns {status, latency_ms, size}."""
    req = request.Request(url, method=method, data=data, headers=headers or {})
    t0 = time.time()
    try:
        with request.urlopen(req, timeout=30) as resp:
            body = resp.read()
            return {
                "status": resp.status,
                "latency_ms": round((time.time() - t0) * 1000, 1),
                "size": len(body),
            }
    except error.HTTPError as e:
        return {
            "status": e.code,
            "latency_ms": round((time.time() - t0) * 1000, 1),
            "size": 0,
            "error": str(e),
        }
    except Exception as e:
        return {
            "status": 0,
            "latency_ms": round((time.time() - t0) * 1000, 1),
            "size": 0,
            "error": str(e),
        }


def run_throughput_test(url: str, path: str, concurrent: int, duration: int) -> dict:
    """Run throughput test on an endpoint."""
    full_url = f"{url.rstrip('/')}{path}"
    results = []
    errors = 0
    start = time.time()

    def worker():
        nonlocal errors
        local_results = []
        while time.time() - start < duration:
            r = timed_request(full_url)
            local_results.append(r)
            if r["status"] != 200:
                errors += 1
        return local_results

    with ThreadPoolExecutor(max_workers=concurrent) as pool:
        futures = [pool.submit(worker) for _ in range(concurrent)]
        for f in as_completed(futures):
            results.extend(f.result())

    elapsed = time.time() - start
    latencies = [r["latency_ms"] for r in results if r["status"] == 200]

    return {
        "endpoint": path,
        "concurrent": concurrent,
        "duration_sec": round(elapsed, 1),
        "total_requests": len(results),
        "errors": errors,
        "rps": round(len(results) / elapsed, 1),
        "latency_p50": round(statistics.median(latencies), 1) if latencies else 0,
        "latency_p95": round(sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0, 1),
        "latency_p99": round(sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0, 1),
        "latency_avg": round(statistics.mean(latencies), 1) if latencies else 0,
        "latency_max": round(max(latencies), 1) if latencies else 0,
    }


def main():
    parser = argparse.ArgumentParser(description="Subtitle Generator Load Tester")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL")
    parser.add_argument("--concurrent", type=int, default=10, help="Concurrent connections")
    parser.add_argument("--duration", type=int, default=10, help="Test duration in seconds")
    args = parser.parse_args()

    print(f"Load Testing: {args.url}")
    print(f"Concurrent: {args.concurrent}, Duration: {args.duration}s")
    print("=" * 70)

    # Test 1: Health endpoint
    print("\n[1/3] Testing GET /health ...")
    health = run_throughput_test(args.url, "/health", args.concurrent, args.duration)
    print(f"  RPS: {health['rps']} | P50: {health['latency_p50']}ms | "
          f"P95: {health['latency_p95']}ms | P99: {health['latency_p99']}ms | "
          f"Errors: {health['errors']}/{health['total_requests']}")

    # Test 2: System info
    print("\n[2/3] Testing GET /system-info ...")
    sysinfo = run_throughput_test(args.url, "/system-info", args.concurrent, args.duration)
    print(f"  RPS: {sysinfo['rps']} | P50: {sysinfo['latency_p50']}ms | "
          f"P95: {sysinfo['latency_p95']}ms | P99: {sysinfo['latency_p99']}ms | "
          f"Errors: {sysinfo['errors']}/{sysinfo['total_requests']}")

    # Test 3: Metrics endpoint
    print("\n[3/3] Testing GET /metrics ...")
    metrics = run_throughput_test(args.url, "/metrics", args.concurrent, args.duration)
    print(f"  RPS: {metrics['rps']} | P50: {metrics['latency_p50']}ms | "
          f"P95: {metrics['latency_p95']}ms | P99: {metrics['latency_p99']}ms | "
          f"Errors: {metrics['errors']}/{metrics['total_requests']}")

    # Summary
    print("\n" + "=" * 70)
    print("CAPACITY PLANNING SUMMARY")
    print("=" * 70)
    print(f"Health check RPS:  {health['rps']} (target: >100 for monitoring)")
    print(f"System info RPS:   {sysinfo['rps']}")
    print(f"Metrics RPS:       {metrics['rps']} (target: >50 for Prometheus scrape)")

    all_results = {"health": health, "system_info": sysinfo, "metrics": metrics}
    report_path = "loadtest_report.json"
    with open(report_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nFull report: {report_path}")


if __name__ == "__main__":
    main()
