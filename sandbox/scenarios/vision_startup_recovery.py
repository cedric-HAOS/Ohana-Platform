"""Phase 5: Agent starts without Vision, diagnoses it and delivers on recovery.

Real ProductionAgent, scheduler, HTTP clients, SQLite outbox, host health,
Tsunade and local Vision/uvicorn. Host metrics and the push transport are
substituted; no service on Konoha is stopped. Intervals are shortened.
"""

from __future__ import annotations

import asyncio
import socket
import sqlite3
import tempfile
import threading
import time
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import uvicorn
from ohana_agent.core.events import EventBus
from ohana_agent.observation.events import HostHealthObserved
from ohana_agent.observation.exporters.durable_vision_client import DurableVisionClient
from ohana_agent.observation.exporters.http_vision_client import HttpVisionClient
from ohana_agent.observation.exporters.vision_observation_mapper import (
    VisionObservationMapper,
)
from ohana_agent.observation.exporters.vision_observation_outbox import (
    VisionObservationOutbox,
)
from ohana_agent.plugins.mqtt.host_health import (
    HostHealthMonitor,
    HostHealthObservationMapper,
    HostHealthReporter,
    SystemHostProbe,
)
from ohana_agent.runtime.administration_bootstrap import TsunadeObservationHandler
from ohana_agent.runtime.agent import ProductionAgent
from ohana_agent.runtime.vision_probe import VisionVitalsProbe
from ohana_agent.scheduler import Scheduler
from ohana_agent.scheduler.interval_trigger import IntervalTrigger
from ohana_agent.scheduler.task import Task
from ohana_agent.tsunade.expertise import TsunadeExpertiseService
from ohana_agent.tsunade.incidents import TsunadeIncidentRepository
from ohana_agent.tsunade.investigations import InvestigationExecutor
from ohana_vision.web.app import create_app
from ohana_vision.web.bootstrap import build_application_context


def _wait(predicate, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if result := predicate():
            return result
        time.sleep(0.025)
    return None


def run() -> dict:
    checks = []
    with tempfile.TemporaryDirectory(prefix="ohana-vision-recovery-") as tmp:
        root = Path(tmp)
        context = build_application_context(database_path=root / "vision.db")
        listener = socket.socket()
        # Reserve a port without listening: initially Vision really refuses HTTP.
        listener.bind(("127.0.0.1", 0))
        base = f"http://127.0.0.1:{listener.getsockname()[1]}"
        server = uvicorn.Server(
            uvicorn.Config(create_app(context=context), log_level="warning")
        )
        vision_thread = threading.Thread(
            target=lambda: asyncio.run(
                server.serve(sockets=[listener]), loop_factory=asyncio.SelectorEventLoop
            ),
            daemon=True,
        )
        http = HttpVisionClient(
            f"{base}/api/observations",
            f"{base}/api/infrastructure",
            timeout_seconds=0.2,
        )
        delivery = DurableVisionClient(
            http, VisionObservationOutbox(root / "outbox.db"), retry_seconds=0.1
        )
        probe = VisionVitalsProbe(
            f"{base}/api/runtime/vitals", interval_seconds=0.1, timeout_seconds=0.2
        )
        systemctl = root / "systemctl"
        systemctl.touch()
        monitor = HostHealthMonitor(
            SystemHostProbe(
                proc_root=root / "proc",
                sys_root=root / "sys",
                systemctl_path=systemctl,
                disk_usage=lambda _: SimpleNamespace(total=100, used=10, free=90),
                runner=lambda command, **_: SimpleNamespace(
                    returncode=0, stdout="0\n" if command[1:2] == ["show"] else ""
                ),
            ),
            vision=probe.latest,
        )
        incidents = TsunadeIncidentRepository(root / "incidents.db")
        expertise = TsunadeExpertiseService(
            incidents=incidents,
            investigations=InvestigationExecutor(
                plugins=None,
                host_health_reader=lambda: monitor.collect().to_dict(),
                vision_status_reader=probe.check_now,
            ),
        )
        pushes = []
        bus = EventBus()
        bus.subscribe(
            HostHealthObserved,
            TsunadeObservationHandler(
                incidents=incidents,
                expertise=expertise,
                administration=SimpleNamespace(),
                logs_config=SimpleNamespace(enabled=False, sources=[]),
                notifications=SimpleNamespace(publish=pushes.append),
            ),
        )
        observed_ids = []
        host_mapper = HostHealthObservationMapper()
        vision_mapper = VisionObservationMapper()

        def publish(snapshot):
            observation = host_mapper.to_observation(snapshot)
            observed_ids.append(str(observation.id))
            bus.publish(HostHealthObserved(observation))
            delivery.send_observation(vision_mapper.to_payload(observation))

        reporter = HostHealthReporter(monitor, sinks=(publish,), interval_seconds=0.15)
        scheduler = Scheduler()
        task = Task(
            command="sandbox.other-component",
            trigger=IntervalTrigger(
                interval=timedelta(seconds=0.1), start_at=datetime.now(UTC)
            ),
        )
        scheduler.add_task(task)
        agent = ProductionAgent(
            scheduler=scheduler,
            vision_client=delivery,
            infrastructure_payload={
                "schema_version": 1,
                "infrastructure_id": "sandbox",
                "name": "Sandbox",
                "environment": "test",
            },
            tick_interval_seconds=0.025,
            infrastructure_retry_seconds=0.1,
            host_health_runtime=reporter,
            vision_export_runtime=delivery,
            vision_probe_runtime=probe,
        )
        agent_thread = threading.Thread(target=agent.run, daemon=True)
        try:
            agent_thread.start()
            incident = _wait(
                lambda: next(
                    (i for i in incidents.list() if i.severity == "critical"), None
                )
            )
            decision = _wait(
                lambda: incident and incidents.get(incident.incident_id).latest_decision
            )
            queued = delivery.pending_count
            checks.append(
                (
                    "Vision absente au démarrage : Agent observe et conserve ses observations",
                    agent.running
                    and not agent.infrastructure_synchronized
                    and task.execution_count > 0
                    and queued > 0,
                )
            )
            checks.append(
                (
                    "Incident HTTP confirmé par vision.status sans IA",
                    bool(decision)
                    and decision.get("decision_source") == "deterministic"
                    and decision.get("epistemic_status") == "confirmed_by_probe"
                    and any(
                        e.kind == "diagnostic"
                        and e.payload.get("failed_investigations") == ["vision.status"]
                        for e in incidents.get(incident.incident_id).events
                    ),
                )
            )
            time.sleep(0.35)
            checks.append(
                (
                    "Panne persistante : un incident et une notification indépendante de Vision",
                    len(incidents.list()) == 1
                    and len([p for p in pushes if p["type"] == "CRITICAL"]) == 1,
                )
            )
            backlog_ids = set(observed_ids)
            vision_thread.start()
            ready = _wait(lambda: server.started)
            recovered = _wait(
                lambda: (
                    incident
                    and agent.infrastructure_synchronized
                    and incidents.get(incident.incident_id).state == "resolved"
                    and delivery.pending_count == 0
                )
            )
            checks.append(
                (
                    "Retour de Vision : synchronisation et résolution du même incident",
                    bool(ready and recovered),
                )
            )
            # Stop producers before checking exact delivery and closing databases.
            agent.request_stop()
            agent_thread.join(timeout=10)
            with closing(sqlite3.connect(root / "vision.db")) as connection:
                received = {
                    row[0]
                    for row in connection.execute(
                        "SELECT observation_id FROM observations"
                    )
                }
            vitals = probe.check_now()
            checks.append(
                (
                    "Toutes les observations de panne sont réellement conservées par Vision",
                    bool(backlog_ids) and backlog_ids <= received,
                )
            )
            checks.append(
                (
                    "Vitaux HTTP : ingestion récente datée à Paris",
                    vitals["available"] is True
                    and vitals["ingestion_silence_seconds"] < 5
                    and vitals["last_ingested_at"].endswith(("+01:00", "+02:00")),
                )
            )
        finally:
            agent.request_stop()
            agent_thread.join(timeout=10)
            server.should_exit = True
            if vision_thread.ident is not None:
                vision_thread.join(timeout=10)
            listener.close()
            context.observation_store.close()
            context.incident_store.close()
            incidents.close()
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": {
            "observations en attente pendant la panne": queued,
            "limites": "Hôte et transport APNs simulés ; HTTP et bases réels, intervalles raccourcis.",
        },
    }
