"""Phase 6, lot 1: why Katsuyu was woken, what it ran, how the cycle ended.

Real Agent HTTP listener, real Katsuyu worker loop and handlers. Only the
Wake-on-LAN sender, the Windows shutdown and the session query are replaced
by recorders, and the Agent clock is driven by the scenario so that the PC
"goes off" without waiting. Nothing on Konoha or on this PC is touched.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from ohana_agent.api.http import AdministrationHTTPServer
from ohana_agent.api.service import AdministrationService
from ohana_agent.infrastructure.repository import InfrastructureConfigurationRepository
from ohana_agent.jobs.repository import DistributedJobRepository
from ohana_katsuyu.handlers import KatsuyuWorkspace, SystemHealthHandler
from ohana_katsuyu.power import ShutdownVeto, session_shutdown_veto
from ohana_katsuyu.worker import AgentClient, KatsuyuWorker

from scenarios._support import SandboxClock

WORKER = "katsuyu-sandbox"
MAC = "AA:BB:CC:DD:EE:FF"
ADMIN_TOKEN = "tsunade-sandbox"
WORKER_TOKEN = "katsuyu-sandbox-secret"
INFRASTRUCTURE_YAML = """\
infrastructure:
  id: ohana-sandbox
  name: Ohana Sandbox
  environment: production
nodes: []
services: []
"""


def _paris(value: object) -> bool:
    return isinstance(value, str) and value.endswith(("+01:00", "+02:00"))


def _worker(server: AdministrationHTTPServer) -> dict[str, Any]:
    host, port = server.address
    request = Request(
        f"http://{host}:{port}/v1/jobs/workers",
        headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
    )
    with urlopen(request, timeout=5) as response:
        return json.load(response)["workers"][0]


def _kinds(server: AdministrationHTTPServer) -> list[str]:
    return [event["kind"] for event in reversed(_worker(server)["power_events"])]


def _queue(jobs: DistributedJobRepository, clock: SandboxClock, number: int) -> None:
    jobs.create(
        {
            "protocol_version": 1,
            "job_id": f"66666666-6666-4666-8666-{number:012d}",
            "type": "system.health",
            "created_at": clock.current.isoformat(),
            "parameters": {},
            "timeout": 3600,
        }
    )


def run() -> dict:
    checks: list[tuple[str, bool]] = []
    details: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-wake-") as tmp:
        root = Path(tmp)
        (root / "infrastructure.yaml").write_text(INFRASTRUCTURE_YAML, encoding="utf-8")
        clock = SandboxClock()
        jobs = DistributedJobRepository(root / "jobs.db", clock=clock)
        wakes: list[str] = []
        service = AdministrationService(
            infrastructure_repository=InfrastructureConfigurationRepository(
                root / "infrastructure.yaml"
            ),
            job_repository=jobs,
            wake_enabled=True,
            wake_sender=wakes.append,
            wake_minimum_interval_seconds=0,
        )
        administration = AdministrationHTTPServer(
            service=service, token=ADMIN_TOKEN, worker_token=WORKER_TOKEN, port=0
        )
        administration.start()
        try:
            host, port = administration.address
            shutdowns: list[str] = []
            veto: list[ShutdownVeto | None] = [None]
            worker = KatsuyuWorker(
                client=AgentClient(f"http://{host}:{port}", WORKER_TOKEN),
                worker_id=WORKER,
                handlers={
                    "system.health": SystemHealthHandler(
                        KatsuyuWorkspace(root / "workspace")
                    )
                },
                heartbeat_seconds=0.2,
                shutdown_requester=lambda: shutdowns.append("shutdown"),
                shutdown_veto=lambda: veto[0],
            )
            jobs.register_worker(
                {
                    "protocol_version": 1,
                    "worker_id": WORKER,
                    "capabilities": ["system.health"],
                    "platform": "Windows 11",
                    "worker_version": "sandbox",
                    "wake_on_lan_mac_address": MAC,
                }
            )

            # --- Cycle 1: nothing prevents the shutdown -------------------
            clock.advance(minutes=30)  # the PC is off: heartbeat long lapsed
            _queue(jobs, clock, 1)
            _queue(jobs, clock, 2)
            woke = service._wake_compatible_worker("system.health")  # noqa: SLF001
            clock.advance(seconds=64)
            worker.register()
            processed = [worker.run_once(), worker.run_once()]
            clock.advance(seconds=5)
            worker.run_once()  # idle: Agent grants the shutdown
            first = _worker(administration)["power_events"]
            by_kind = {event["kind"]: event for event in first}
            checks += [
                (
                    "réveil envoyé à l'adresse MAC annoncée",
                    woke and wakes == [MAC],
                ),
                (
                    "cycle complet journalisé : réveil, connexion, arrêt accordé, arrêt lancé",
                    _kinds(administration)
                    == [
                        "wake_sent",
                        "worker_online",
                        "shutdown_granted",
                        "shutdown_started",
                    ],
                ),
                (
                    "raison du réveil : deux travaux system.health en attente",
                    by_kind["wake_sent"]["detail"]
                    == {
                        "trigger": "queued_jobs",
                        "pending_jobs": {"system.health": 2},
                        "timeout_seconds": 180,
                    },
                ),
                (
                    "délai de connexion mesuré (64 s) et travail exécuté compté",
                    by_kind["worker_online"]["detail"] == {"after_seconds": 64}
                    and by_kind["shutdown_granted"]["detail"]
                    == {"executed": {"system.health": 2}, "failed": 0}
                    and processed == [True, True],
                ),
                (
                    "arrêt Windows demandé une seule fois, après le rapport à l'Agent",
                    shutdowns == ["shutdown"] and worker.shutdown_requested,
                ),
                (
                    "dates du journal à l'heure de Paris",
                    all(_paris(event["occurred_at"]) for event in first),
                ),
            ]

            # --- Cycle 2: someone is signed in -> the PC stays on ---------
            shutdowns.clear()
            veto[0] = ShutdownVeto("interactive_session", 1)
            worker = KatsuyuWorker(
                client=AgentClient(f"http://{host}:{port}", WORKER_TOKEN),
                worker_id=WORKER,
                handlers=worker.handlers,
                heartbeat_seconds=0.2,
                shutdown_requester=lambda: shutdowns.append("shutdown"),
                shutdown_veto=lambda: veto[0],
            )
            clock.advance(hours=3)
            _queue(jobs, clock, 3)
            service._wake_compatible_worker("system.health")  # noqa: SLF001
            clock.advance(seconds=40)
            worker.register()
            worker.run_once()
            clock.advance(seconds=5)
            worker.run_once()  # granted, then vetoed by the session
            after_veto = _worker(administration)
            newest = after_veto["power_events"][0]
            checks += [
                (
                    "session ouverte : pas d'arrêt, la raison est journalisée",
                    shutdowns == []
                    and not worker.shutdown_requested
                    and newest["kind"] == "shutdown_vetoed"
                    and newest["detail"]
                    == {"reason": "interactive_session", "sessions": 1},
                ),
                (
                    "le PC laissé allumé reste disponible pour le worker",
                    after_veto["availability"] == "AVAILABLE",
                ),
            ]

            # --- Reuse: an available worker is never woken again ----------
            wakes_before = len(wakes)
            events_before = len(after_veto["power_events"])
            clock.advance(seconds=10)
            _queue(jobs, clock, 4)
            woke_again = service._wake_compatible_worker("system.health")  # noqa: SLF001
            worker.run_once()
            clock.advance(seconds=5)
            worker.run_once()
            after_reuse = _worker(administration)
            checks += [
                (
                    "worker déjà disponible : réutilisé sans nouveau réveil",
                    not woke_again
                    and len(wakes) == wakes_before
                    and jobs.get("66666666-6666-4666-8666-000000000004").status.value
                    == "SUCCEEDED",
                ),
                (
                    "la permission d'arrêt était consommée : aucun arrêt ni nouveau cycle",
                    shutdowns == []
                    and len(after_reuse["power_events"]) == events_before,
                ),
            ]

            # --- The real session query works on this machine -------------
            real = session_shutdown_veto()
            checks.append(
                (
                    "requête de sessions Windows réelle : réponse exploitable",
                    real is None or real.reason in {"interactive_session", "session_check_failed"},
                )
            )
            details["cycle"] = " → ".join(_kinds(administration)[:4])
            details["veto"] = f"{newest['detail']}"
            details["sessions réelles sur ce PC"] = (
                "aucune" if real is None else f"{real.reason} ({real.sessions})"
            )
        finally:
            administration.stop()
            jobs.close()
    details["portée"] = (
        "Agent HTTP et worker Katsuyu réels ; Wake-on-LAN, arrêt Windows et "
        "sessions injectés, horloge de l'Agent pilotée"
    )
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
