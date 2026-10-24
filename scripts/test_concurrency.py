import json
import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_URL = os.getenv(
    "SAFEAGENT_EXECUTE_URL",
    "http://localhost:8081/api/runs/execute"
)
OUTPUT = Path("reports/concurrency_local_test.json")
LOCK = threading.Lock()


def run_job(index):
    sandbox_name = f"sbx-{uuid.uuid4().hex[:12]}"
    run_id = f"concurrency-{uuid.uuid4().hex}"
    started_at = datetime.now(timezone.utc).isoformat()
    started = time.monotonic()

    payload = {
        "sandbox_name": sandbox_name,
        "run_id": run_id,
        "problem_id": "concurrency-test",
        "command": "echo SafeAgent-concurrency-test",
        "timeout": 20
    }

    result = {
        "sandbox_name": sandbox_name,
        "started_at": started_at,
        "success": False,
        "http_status": None,
        "wall_clock_s": None,
        "error": None
    }

    try:
        request = Request(
            API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urlopen(request, timeout=40) as response:
            result["http_status"] = response.status
            body = json.loads(response.read().decode("utf-8"))

        result["success"] = body.get("state") == "succeeded"
        if not result["success"]:
            result["error"] = body.get("error_details") or body.get("state")

    except HTTPError as exc:
        result["http_status"] = exc.code
        result["error"] = exc.read().decode("utf-8", errors="replace")[:500]
    except (URLError, TimeoutError, OSError) as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"

    result["wall_clock_s"] = round(time.monotonic() - started, 3)
    print(
        f"Job {index}: {sandbox_name} | "
        f"success={result['success']} | error={result['error']}"
    )
    return result


def main():
    jobs = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_job, i) for i in range(1, 6)]
        for future in as_completed(futures):
            jobs.append(future.result())

    report = {
        "test_type": "local_api_concurrency",
        "api_url": API_URL,
        "required_concurrent_jobs": 5,
        "completed_jobs": len(jobs),
        "jobs": jobs,
        "breakage_notes": (
            "This test sends five concurrent requests to the SafeAgent API. "
            "It measures API behavior, not proof that five Celesto cloud "
            "sandboxes ran concurrently. Review each job's result and error."
        )
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"\nSaved local API test results to {OUTPUT.resolve()}")
    print(f"Successful jobs: {sum(job['success'] for job in jobs)}/{len(jobs)}")


if __name__ == "__main__":
    main()
