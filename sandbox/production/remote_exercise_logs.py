from __future__ import annotations

import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ADMIN_PORT = int(sys.argv[1])
JOBS_DB = sys.argv[2]
TIMEOUT_SECONDS = int(sys.argv[3])

BASE_URL = f"http://127.0.0.1:{ADMIN_PORT}"
TOKEN_FILE = Path("/etc/ohana-agent/management.token")

TERMINAL = {
    "SUCCEEDED",
    "FAILED",
    "CANCELLED",
    "TIMEOUT",
}


def api(method: str, path: str) -> dict[str, object]:
    token = TOKEN_FILE.read_text(
        encoding="utf-8"
    ).strip()

    request = urllib.request.Request(
        BASE_URL + path,
        data=b"" if method == "POST" else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        method=method,
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=10,
        ) as response:
            return json.loads(
                response.read().decode("utf-8")
            )
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"HTTP {exc.code}: {body}"
        ) from exc


def job_completion(
    job_id: str,
) -> tuple[int | None, int]:
    connection = sqlite3.connect(
        f"file:{JOBS_DB}?mode=ro",
        uri=True,
        timeout=2,
    )
    connection.execute("PRAGMA query_only=ON")

    row = connection.execute(
        """
        SELECT completion_processed
        FROM distributed_jobs
        WHERE job_id = ?
        """,
        (job_id,),
    ).fetchone()

    active_logs = connection.execute(
        """
        SELECT COUNT(*)
        FROM distributed_jobs
        WHERE type = 'logs.health_check'
          AND status IN (
              'QUEUED',
              'WAITING_WORKER',
              'RUNNING'
          )
        """
    ).fetchone()[0]

    connection.close()

    return (
        int(row[0]) if row is not None else None,
        int(active_logs),
    )


workers = api(
    "GET",
    "/v1/jobs/workers",
)

compatible = [
    worker
    for worker in workers.get("workers", [])
    if (
        worker.get("availability") == "AVAILABLE"
        and "logs.health_check"
        in worker.get("capabilities", [])
    )
]

if not compatible:
    print(
        json.dumps(
            {
                "passed": False,
                "exercised": False,
                "reason": (
                    "Aucun worker Katsuyu AVAILABLE "
                    "compatible logs.health_check."
                ),
            },
            ensure_ascii=False,
        )
    )
    raise SystemExit(0)


created = api(
    "POST",
    "/v1/incidents/logs/check",
)

job_id = str(created["job_id"])
deadline = (
    time.monotonic() + TIMEOUT_SECONDS
)

job = created

while time.monotonic() < deadline:
    job = api(
        "GET",
        f"/v1/jobs/{job_id}",
    )

    if job.get("status") in TERMINAL:
        break

    time.sleep(2)


status = str(job.get("status") or "")

if status not in TERMINAL:
    print(
        json.dumps(
            {
                "passed": False,
                "exercised": True,
                "job_id": job_id,
                "status": status,
                "reason": (
                    "Délai du test dépassé avant "
                    "l'état terminal."
                ),
            },
            ensure_ascii=False,
        )
    )
    raise SystemExit(0)


completion_processed = None
active_logs = -1

while time.monotonic() < deadline:
    (
        completion_processed,
        active_logs,
    ) = job_completion(job_id)

    if completion_processed == 1:
        break

    time.sleep(1)


passed = (
    status == "SUCCEEDED"
    and completion_processed == 1
    and active_logs == 0
)

print(
    json.dumps(
        {
            "passed": passed,
            "exercised": True,
            "job_id": job_id,
            "status": status,
            "worker_id": job.get("worker_id"),
            "finished_at": job.get("finished_at"),
            "completion_processed": (
                completion_processed
            ),
            "active_log_jobs": active_logs,
            "error": job.get("error"),
        },
        ensure_ascii=False,
    )
)