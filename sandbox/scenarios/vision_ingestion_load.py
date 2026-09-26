"""Vision under Konoha's observation load with pages open.

A real Vision server (uvicorn) on a two-day database shaped like INFRA-01 on
26 September: about 26,000 observations a day, mostly Z-Wave node and
network presence checks with ~740 bytes of metadata. The Agent posts one
observation a second while two open pages reload the 24 h timeline after
each accepted observation, as Vision 1.26.0 pages did. On INFRA-01 that
timeline took about 18 s to build, Vision stayed at full CPU and the Agent's
observation deliveries timed out.
"""

from __future__ import annotations

import asyncio
import json
import random
import socket
import sqlite3
import statistics
import tempfile
import threading
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import uvicorn

from ohana_vision.domain.observation_store import ObservationStore
from ohana_vision.web.app import create_app
from ohana_vision.web.bootstrap import build_application_context

OBSERVATIONS = 20
PAGES = 2
# Thresholds for a desktop Sandbox; INFRA-01 is several times slower.
INGESTION_P95_MS = 250
TIMELINE_P95_MS = 300
PADDING = "x" * 520


def _identities():
    items = [
        (f"zwave-zwave-node-{node}", "zwave.node.alive", 120, "device")
        for node in range(2, 22)
    ]
    items += [(f"dev-{index:02d}", "network.reachable", 300, "device") for index in range(23)]
    items += [
        (name, capability, interval, "service")
        for name, capability, interval in (
            ("dns-primary", "dns.resolve", 120),
            ("dns-secondaire", "dns.resolve", 120),
            ("mqtt", "mqtt.roundtrip", 120),
            ("zwave", "zwave.status", 120),
            ("tic-linky", "teleinformation.freshness", 60),
            ("ohana-host", "host.health", 60),
            ("mesure-puissance", "home_assistant.telemetry.freshness", 300),
            ("wireguard", "wireguard.status", 300),
            ("chrony", "ntp.query", 3600),
            ("dhcp", "dhcp.status", 1800),
        )
    ]
    return items


def _metadata(name: str, kind: str) -> dict:
    metadata = {"device_id": name, "padding": PADDING}
    if kind == "device":
        metadata["target_type"] = "device"
    return metadata


def _populate(database: Path, now: datetime) -> int:
    ObservationStore(database, retention_days=2).close()  # current schema
    rng = random.Random(7)
    rows = []
    for name, capability, interval, kind in _identities():
        node = name if kind == "device" else "infra-01"
        metadata = json.dumps(_metadata(name, kind), separators=(",", ":"), sort_keys=True)
        at = now - timedelta(days=2) + timedelta(seconds=rng.randint(0, interval))
        while at < now:
            status = (
                "unavailable"
                if capability == "network.reachable" and rng.random() < 0.01
                else "healthy"
            )
            rows.append(
                (str(uuid4()), capability, name, node, status, at.isoformat(),
                 f"{capability} ok", 3.2, metadata)
            )
            at += timedelta(seconds=interval)
    rows.sort(key=lambda row: row[5])
    with sqlite3.connect(database) as connection:
        connection.executemany(
            """INSERT INTO observations (observation_id, capability_id, service_id,
            node_id, status, observed_at, message, latency_ms, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )
    return len(rows)


def _request(url: str, payload: dict | None = None, timeout: float = 30) -> float:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        response.read()
    return (time.perf_counter() - started) * 1000


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))]


def run() -> dict:
    now = datetime.now(UTC).replace(microsecond=0)
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-vision-load-") as tmp:
        database = Path(tmp) / "vision.db"
        stored = _populate(database, now)
        context = build_application_context(database_path=database, retention_days=2)
        app = create_app(context=context)
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(128)
        base = f"http://127.0.0.1:{listener.getsockname()[1]}"
        server = uvicorn.Server(uvicorn.Config(app, log_level="warning"))
        thread = threading.Thread(
            target=lambda: asyncio.run(
                server.serve(sockets=[listener]), loop_factory=asyncio.SelectorEventLoop
            ),
            daemon=True,
        )
        thread.start()
        deadline = time.monotonic() + 20
        while not server.started and time.monotonic() < deadline:
            time.sleep(0.05)

        since = urllib.parse.quote((now - timedelta(hours=24)).isoformat())
        timeline_url = f"{base}/api/timeline?since={since}"
        ingestion: list[float] = []
        timelines: list[float] = []
        errors: list[str] = []
        accepted = threading.Condition()
        accepted_count = [0]
        done = threading.Event()

        def page() -> None:
            seen = 0
            while not done.is_set():
                with accepted:
                    accepted.wait_for(lambda: accepted_count[0] > seen or done.is_set(), 1)
                    target = accepted_count[0]
                if target == seen:
                    continue
                seen = target
                try:
                    timelines.append(_request(timeline_url))
                except Exception as error:  # noqa: BLE001
                    errors.append(f"timeline {type(error).__name__}")

        pages = [threading.Thread(target=page, daemon=True) for _ in range(PAGES)]
        for item in pages:
            item.start()
        identities = _identities()
        try:
            for index in range(OBSERVATIONS):
                name, capability, _interval, kind = identities[index % len(identities)]
                payload = {
                    "capability_id": capability,
                    "service_id": name,
                    "node_id": name if kind == "device" else "infra-01",
                    "status": "healthy",
                    "observed_at": (now + timedelta(seconds=index + 1)).isoformat(),
                    "observation_id": str(uuid4()),
                    "message": f"{capability} ok",
                    "latency_ms": 3.2,
                    "metadata": _metadata(name, kind),
                }
                started = time.perf_counter()
                try:
                    # The Agent's durable client gives up after 5 s.
                    ingestion.append(_request(f"{base}/api/observations", payload, 5))
                except Exception as error:  # noqa: BLE001
                    errors.append(f"ingestion {type(error).__name__}")
                with accepted:
                    accepted_count[0] += 1
                    accepted.notify_all()
                time.sleep(max(0.0, 1.0 - (time.perf_counter() - started)))
        finally:
            done.set()
            with accepted:
                accepted.notify_all()
            for item in pages:
                item.join(timeout=60)
            server.should_exit = True
            thread.join(timeout=15)
            context.observation_store.close()
            context.incident_store.close()

    ingestion_p95 = _p95(ingestion) if ingestion else float("inf")
    timeline_p95 = _p95(timelines) if timelines else float("inf")
    checks = [
        (
            f"ingestion à 1 observation/s, 2 pages ouvertes : p95 < {INGESTION_P95_MS} ms",
            ingestion_p95 < INGESTION_P95_MS and not any("ingestion" in e for e in errors),
        ),
        (
            f"chronologie 24 h redemandée à chaque observation : p95 < {TIMELINE_P95_MS} ms",
            timeline_p95 < TIMELINE_P95_MS and not any("timeline" in e for e in errors),
        ),
    ]
    return {
        "passed": all(passed for _, passed in checks),
        "checks": checks,
        "details": {
            "observations en base": stored,
            "ingestion p95 / médiane (ms)": (
                f"{ingestion_p95:.0f} / {statistics.median(ingestion):.0f}"
                if ingestion
                else "aucune"
            ),
            "chronologie p95 / médiane (ms)": (
                f"{timeline_p95:.0f} / {statistics.median(timelines):.0f}"
                if timelines
                else "aucune"
            ),
            "chronologies servies": len(timelines),
            "erreurs": ", ".join(sorted(set(errors))) or "aucune",
        },
    }
