import asyncio
import httpx
import time
import statistics

# Configuration
BASE_URL = "http://127.0.0.1:8001"
CONCURRENCY = 100
DURATION = 5  # seconds

async def worker(client, url, stop_event, results):
    while not stop_event.is_set():
        start = time.perf_counter()
        try:
            resp = await client.get(url)
            elapsed = time.perf_counter() - start
            results.append({"status": resp.status_code, "time": elapsed})
        except Exception as e:
            results.append({"status": "error", "time": 0})

async def run_load_test(endpoint, label):
    print(f"\n--- Testing: {label} ({endpoint}) ---")
    print(f"Concurrency: {CONCURRENCY}, Duration: {DURATION}s")
    
    url = f"{BASE_URL}{endpoint}"
    results = []
    stop_event = asyncio.Event()
    
    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=CONCURRENCY)) as client:
        # Warmup
        try:
            await client.get(url)
        except Exception:
            print("Server not reachable! Is uvicorn running on port 8001?")
            return

        tasks = [asyncio.create_task(worker(client, url, stop_event, results)) for _ in range(CONCURRENCY)]
        
        # Run for DURATION
        await asyncio.sleep(DURATION)
        stop_event.set()
        await asyncio.gather(*tasks)

    # Analysis
    count = len(results)
    if count == 0:
        print("No requests completed.")
        return

    success = [r for r in results if r["status"] == 200]
    errors = [r for r in results if r["status"] != 200]
    times = [r["time"] for r in success]
    
    rps = count / DURATION
    avg_latency = statistics.mean(times) * 1000 if times else 0
    p95 = statistics.quantiles(times, n=20)[18] * 1000 if len(times) >= 20 else 0
    
    print(f"Total Requests: {count}")
    print(f"RPS: {rps:.2f} req/sec")
    print(f"Success: {len(success)}")
    print(f"Errors: {len(errors)}")
    print(f"Avg Latency: {avg_latency:.2f} ms")
    print(f"P95 Latency: {p95:.2f} ms")

async def main():
    # 1. Test Framework Overhead (Root Route)
    await run_load_test("/", "Root Route (Framework Overhead)")
    
    # 2. Test DB Read (Items)
    # Ensure at least one item exists
    async with httpx.AsyncClient() as client:
        await client.post(f"{BASE_URL}/items", json={"name": "LoadTestItem"})
        
    await run_load_test("/items", "DB Read (List Items)")

if __name__ == "__main__":
    asyncio.run(main())
