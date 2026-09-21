# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import socket
import sqlite3
import subprocess
import sys
from pathlib import Path


SERVICE = sys.argv[1]
AGENT_BIN = sys.argv[2]
JOBS_DB = sys.argv[3]
ADMIN_PORT = int(sys.argv[4])
JOURNAL_MINUTES = int(sys.argv[5])


def command(arguments: list[str]) -> dict[str, object]:
    try:
        completed = subprocess.run(
            arguments,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except OSError as exc:
        return {
            "returncode": getattr(exc, "errno", 1) or 1,
            "stdout": "",
            "stderr": (
                f"{type(exc).__name__}: {exc}"
            ),
        }

    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def installed_version() -> dict[str, object]:
    return command(
        [
            "sudo",
            "-n",
            "-u",
            "ohana-agent",
            AGENT_BIN,
            "--version",
        ]
    )

def service_state() -> dict[str, object]:
    result = command(
        [
            "systemctl",
            "show",
            SERVICE,
            "--property=ActiveState",
            "--property=SubState",
            "--property=NRestarts",
            "--property=Result",
            "--property=ExecMainStatus",
            "--property=ExecMainStartTimestamp",
            "--no-pager",
        ]
    )

    properties: dict[str, str] = {}

    if result["returncode"] == 0:
        for line in str(result["stdout"]).splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                properties[key] = value

    return {
        "ok": result["returncode"] == 0,
        "properties": properties,
        "stderr": result["stderr"],
    }


def administration_state() -> dict[str, object]:
    try:
        with socket.create_connection(
            ("127.0.0.1", ADMIN_PORT),
            timeout=2,
        ):
            return {"ok": True}
    except OSError as exc:
        return {
            "ok": False,
            "error": type(exc).__name__,
        }


def jobs_state() -> dict[str, object]:
    script = f"""
import json
import sqlite3

path = {JOBS_DB!r}

connection = sqlite3.connect(
    f"file:{{path}}?mode=ro",
    uri=True,
    timeout=2,
)
connection.row_factory = sqlite3.Row
connection.execute("PRAGMA query_only=ON")

active = connection.execute(
    \"\"\"
    SELECT job_id, type, status, created_at
    FROM distributed_jobs
    WHERE status IN (
        'QUEUED',
        'WAITING_WORKER',
        'RUNNING'
    )
    ORDER BY julianday(created_at), job_id
    \"\"\"
).fetchall()

pending = connection.execute(
    \"\"\"
    SELECT job_id, type, status, finished_at
    FROM distributed_jobs
    WHERE completion_processed = 0
    ORDER BY julianday(finished_at), job_id
    \"\"\"
).fetchall()

latest = connection.execute(
    \"\"\"
    SELECT
        type,
        status,
        created_at,
        finished_at,
        completion_processed
    FROM distributed_jobs
    ORDER BY julianday(created_at) DESC, job_id DESC
    LIMIT 5
    \"\"\"
).fetchall()

connection.close()

print(
    json.dumps(
        {{
            "active": [dict(row) for row in active],
            "pending": [dict(row) for row in pending],
            "latest": [dict(row) for row in latest],
        }}
    )
)
"""

    result = subprocess.run(
        [
            "sudo",
            "-n",
            "-u",
            "ohana-agent",
            "python3",
            "-",
        ],
        input=script,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    if result.returncode != 0:
        return {
            "ok": False,
            "error": result.stderr.strip(),
        }

    try:
        payload = json.loads(
            result.stdout.strip()
        )
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "error": (
                "Réponse SQLite invalide : "
                f"{type(exc).__name__}: {exc}"
            ),
        }

    return {
        "ok": True,
        **payload,
    }

def journal_state() -> dict[str, object]:
    arguments = [
        "journalctl",
        "-u",
        SERVICE,
        "--since",
        f"{JOURNAL_MINUTES} minutes ago",
        "-p",
        "err..alert",
        "--no-pager",
        "--output=short-iso",
        "-n",
        "50",
    ]

    result = command(arguments)
    stderr = str(result["stderr"]).lower()

    denied = any(
        marker in stderr
        for marker in (
            "permission",
            "not seeing messages",
            "no journal files were opened",
        )
    )

    if result["returncode"] != 0 or denied:
        fallback = command(
            ["sudo", "-n", *arguments]
        )

        if fallback["returncode"] == 0:
            result = fallback
        else:
            return {
                "ok": False,
                "errors": [],
                "stderr": (
                    f"{result['stderr']} | "
                    f"sudo: {fallback['stderr']}"
                ),
            }

    errors = [
        line
        for line in str(result["stdout"]).splitlines()
        if line.strip()
        and "-- No entries --" not in line
    ]

    return {
        "ok": True,
        "errors": errors,
        "stderr": result["stderr"],
    }


print(
    json.dumps(
        {
            "hostname": socket.gethostname(),
            "version": installed_version(),
            "service": service_state(),
            "administration": (
                administration_state()
            ),
            "jobs": jobs_state(),
            "journal": journal_state(),
        },
        ensure_ascii=False,
    )
)