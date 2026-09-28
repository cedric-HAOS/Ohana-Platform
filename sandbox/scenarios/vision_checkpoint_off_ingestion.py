"""The observation request never copies the SQLite WAL into vision.db.

On 28 September the Agent's deliveries to Vision timed out every four
minutes on INFRA-01. SQLite checkpoints automatically inside the commit that
crosses 1000 WAL pages; that checkpoint syncs vision.db and took over five
seconds on the SD card while the observation request waited. Each timeout
followed a vision.db write by exactly the Agent's 5 s deadline.

The Sandbox disk is fast, so the scenario checks the mechanism rather than a
latency: a real Vision server receives enough observations to cross the
automatic checkpoint threshold several times, and vision.db must not change
while an observation request is in flight. The WAL must still reach vision.db
once Vision closes its stores.
"""

from __future__ import annotations

import asyncio
import json
import socket
import sqlite3
import tempfile
import threading
import time
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import uvicorn

from ohana_vision.domain.observation_store import ObservationStore
from ohana_vision.web.app import create_app
from ohana_vision.web.bootstrap import build_application_context

# About 7 WAL frames per observation (table + indexes): 600 observations cross
# the 1000-frame automatic checkpoint threshold several times.
OBSERVATIONS = 600
PADDING = "x" * 520


def _post(url: str, payload: dict) -> None:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    # The Agent's durable client gives up after 5 s.
    with urllib.request.urlopen(request, timeout=5) as response:
        response.read()


def _main_file_rows(database: Path) -> int:
    """Count observations already copied from the WAL into vision.db."""
    connection = sqlite3.connect(f"file:{database}?mode=ro&immutable=1", uri=True)
    try:
        return int(connection.execute("SELECT COUNT(*) FROM observations").fetchone()[0])
    except sqlite3.OperationalError:
        return 0
    finally:
        connection.close()


def run() -> dict:
    now = datetime.now(UTC).replace(microsecond=0)
    # A background checkpoint must not land during a request by chance.
    original_interval = getattr(ObservationStore, "_CHECKPOINT_INTERVAL_SECONDS", None)
    if original_interval is not None:
        ObservationStore._CHECKPOINT_INTERVAL_SECONDS = 3600.0
    written_during_request = 0
    errors: list[str] = []
    try:
        with tempfile.TemporaryDirectory(prefix="ohana-sandbox-checkpoint-") as tmp:
            database = Path(tmp) / "vision.db"
            context = build_application_context(database_path=database, retention_days=2)
            app = create_app(context=context)
            listener = socket.socket()
            listener.bind(("127.0.0.1", 0))
            listener.listen(128)
            url = f"http://127.0.0.1:{listener.getsockname()[1]}/api/observations"
            server = uvicorn.Server(uvicorn.Config(app, log_level="warning"))
            thread = threading.Thread(
                target=lambda: asyncio.run(
                    server.serve(sockets=[listener]),
                    loop_factory=asyncio.SelectorEventLoop,
                ),
                daemon=True,
            )
            thread.start()
            deadline = time.monotonic() + 20
            while not server.started and time.monotonic() < deadline:
                time.sleep(0.05)
            try:
                for index in range(OBSERVATIONS):
                    name = f"zwave-zwave-node-{index % 20 + 2}"
                    before = database.stat().st_size
                    try:
                        _post(
                            url,
                            {
                                "capability_id": "zwave.node.alive",
                                "service_id": name,
                                "node_id": name,
                                "status": "healthy",
                                "observed_at": (
                                    now + timedelta(seconds=index)
                                ).isoformat(),
                                "observation_id": str(uuid4()),
                                "message": "zwave.node.alive ok",
                                "latency_ms": 3.2,
                                "metadata": {"device_id": name, "padding": PADDING},
                            },
                        )
                    except Exception as error:  # noqa: BLE001
                        errors.append(type(error).__name__)
                    # Checkpoints append the new pages: vision.db grows.
                    if database.stat().st_size != before:
                        written_during_request += 1
            finally:
                server.should_exit = True
                thread.join(timeout=15)
                # Keeps SQLite from checkpointing when the observation
                # connection closes: only Vision's own checkpoint counts.
                keeper = sqlite3.connect(database)
                context.observation_store.close()
                copied_on_close = _main_file_rows(database)
                context.incident_store.close()
                keeper.close()
    finally:
        if original_interval is not None:
            ObservationStore._CHECKPOINT_INTERVAL_SECONDS = original_interval

    checks = [
        (
            f"{OBSERVATIONS} observations acceptées sans timeout",
            not errors,
        ),
        (
            "vision.db jamais écrit pendant une requête d'ingestion",
            written_during_request == 0,
        ),
        (
            "le WAL est recopié dans vision.db à l'arrêt de Vision",
            copied_on_close == OBSERVATIONS,
        ),
    ]
    return {
        "passed": all(passed for _, passed in checks),
        "checks": checks,
        "details": {
            "requêtes ayant écrit vision.db": written_during_request,
            "observations dans vision.db à l'arrêt": copied_on_close,
            "erreurs": ", ".join(sorted(set(errors))) or "aucune",
        },
    }
