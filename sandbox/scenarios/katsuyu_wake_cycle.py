"""Phase 6, lots 1 and 2: Katsuyu's wake cycles, explained and measured.

Lot 1: why Katsuyu was woken, what it ran, how the cycle ended (shutdown or
session veto). Lot 2: a PC that never answers is woken again, then abandoned
explicitly, and the reliability of Wake-on-LAN is measured.

Real Agent HTTP listener, real Katsuyu worker loop and handlers. Only the
Wake-on-LAN sender, the Windows shutdown and the session query are replaced
by recorders, and the Agent clock is driven by the scenario so that the PC
"goes off" without waiting. Nothing on Konoha or on this PC is touched.
"""

from __future__ import annotations

import json
import socket
import tempfile
import threading
import time
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from ohana_agent.api.http import AdministrationHTTPServer
from ohana_agent.api.service import AdministrationService
from ohana_agent.infrastructure.repository import InfrastructureConfigurationRepository
from ohana_agent.jobs.repository import DistributedJobRepository
from ohana_agent.jobs.wake_on_lan import WakeOnLanSender
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


def _queue(
    jobs: DistributedJobRepository,
    clock: SandboxClock,
    number: int,
    timeout: int = 3600,
) -> None:
    jobs.create(
        {
            "protocol_version": 1,
            "job_id": f"66666666-6666-4666-8666-{number:012d}",
            "type": "system.health",
            "created_at": clock.current.isoformat(),
            "parameters": {},
            "timeout": timeout,
        }
    )


class _MagicPacketListener:
    """Receive what the real Wake-on-LAN sender puts on a real UDP socket."""

    def __init__(self) -> None:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind(("127.0.0.1", 0))
        self._socket.settimeout(0.2)
        self.port = self._socket.getsockname()[1]
        self.packets: list[bytes] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def _listen(self) -> None:
        while not self._stop.is_set():
            try:
                self.packets.append(self._socket.recvfrom(512)[0])
            except TimeoutError:
                continue
            except OSError:
                return

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2)
        self._socket.close()


def run() -> dict:
    checks: list[tuple[str, bool]] = []
    details: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-wake-") as tmp:
        root = Path(tmp)
        (root / "infrastructure.yaml").write_text(INFRASTRUCTURE_YAML, encoding="utf-8")
        clock = SandboxClock()
        jobs = DistributedJobRepository(root / "jobs.db", clock=clock)
        wakes: list[str] = []
        listener = _MagicPacketListener()

        def send(mac: str) -> None:
            wakes.append(mac)
            WakeOnLanSender(
                mac_address=mac,
                broadcast_address="127.0.0.1",
                port=listener.port,
                burst_count=3,
                burst_interval_seconds=0.01,
            ).send()

        service = AdministrationService(
            infrastructure_repository=InfrastructureConfigurationRepository(
                root / "infrastructure.yaml"
            ),
            job_repository=jobs,
            wake_enabled=True,
            wake_sender=send,
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
                        "attempt": 1,
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

            # --- Lot 2: a PC that never answers ---------------------------
            silent_before = len(wakes)
            clock.advance(hours=2)
            _queue(jobs, clock, 5, timeout=6 * 3600)
            service._wake_compatible_worker("system.health")  # noqa: SLF001
            for _ in range(3):
                clock.advance(seconds=181)
                service.dispatch_due_wake_requests()  # settles the wait
                clock.advance(seconds=600)
                service.dispatch_due_wake_requests()  # retry when due
            silent = _worker(administration)
            silent_kinds = [e["kind"] for e in reversed(silent["power_events"])][-7:]
            tries = [
                e["detail"]["trigger"]
                for e in reversed(silent["power_events"])
                if e["kind"] == "wake_sent"
            ][-3:]
            clock.advance(hours=1)
            service.dispatch_due_wake_requests()
            checks += [
                (
                    "PC muet : deux relances après la première tentative, puis abandon explicite",
                    silent_kinds
                    == [
                        "wake_sent",
                        "wake_timeout",
                        "wake_sent",
                        "wake_timeout",
                        "wake_sent",
                        "wake_timeout",
                        "wake_abandoned",
                    ]
                    and tries == ["queued_jobs", "retry", "retry"],
                ),
                (
                    "pas de quatrième tentative : le travail suit son propre délai",
                    len(wakes) - silent_before == 3
                    and jobs.get("66666666-6666-4666-8666-000000000005").status.value
                    in {"QUEUED", "WAITING_WORKER"},
                ),
                (
                    "aucun arrêt ni incident : un PC qui ne répond pas reste informatif",
                    shutdowns == [],
                ),
            ]

            # --- Someone starts the PC by hand much later -----------------
            worker.register()
            worker.run_once()  # runs the waiting job
            clock.advance(seconds=5)
            worker.run_once()
            after_manual = _worker(administration)
            manual = after_manual["power_events"][0]
            stats = after_manual["wake_stats"]
            checks += [
                (
                    "démarrage manuel long après : journalisé « manual », pas compté comme réponse",
                    manual["kind"] == "worker_online"
                    and manual["detail"] == {"manual": True},
                ),
                (
                    "le travail en attente est exécuté, sans arrêt automatique du PC",
                    jobs.get("66666666-6666-4666-8666-000000000005").status.value
                    == "SUCCEEDED"
                    and shutdowns == [],
                ),
                (
                    "fiabilité mesurée : 5 réveils, 2 à l'heure, 3 sans réponse, 1 abandon",
                    (
                        stats["attempts"],
                        stats["on_time"],
                        stats["unanswered"],
                        stats["abandoned"],
                    )
                    == (5, 2, 3, 1)
                    and stats["median_seconds"] == 64,
                ),
            ]

            # --- The real sender put real magic packets on a real socket ---
            time.sleep(0.5)
            magic = b"\xff" * 6 + bytes.fromhex(MAC.replace(":", "")) * 16
            checks.append(
                (
                    "paquets magiques réels reçus sur une socket UDP : 3 par réveil, "
                    "6 × FF puis 16 × l'adresse MAC",
                    len(listener.packets) == 3 * len(wakes)
                    and all(packet == magic for packet in listener.packets),
                )
            )

            # --- The real session query works on this machine -------------
            real = session_shutdown_veto()
            checks.append(
                (
                    "requête de sessions Windows réelle : réponse exploitable",
                    real is None or real.reason in {"interactive_session", "session_check_failed"},
                )
            )
            details["cycle"] = " → ".join(_kinds(administration)[:4])
            details["fiabilité du réveil"] = str(stats)
            details["veto"] = f"{newest['detail']}"
            details["sessions réelles sur ce PC"] = (
                "aucune" if real is None else f"{real.reason} ({real.sessions})"
            )
        finally:
            listener.close()
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
