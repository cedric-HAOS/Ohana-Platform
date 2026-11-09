"""Prise connectée de Bubule : alimentée avant le réveil, coupée une fois éteint.

Agent HTTP et worker Katsuyu réels, vrai client Home Assistant (HTTP réel vers
un Home Assistant simulé qui tient l'état de la prise et sa consommation), vrai
émetteur Wake-on-LAN (paquets réels sur une socket UDP locale). Seuls l'arrêt
Windows, les sessions et l'horloge de l'Agent sont simulés. Rien n'est envoyé
à la vraie prise ni à Konoha.
"""

from __future__ import annotations

import json
import socket
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from ohana_agent.api.http import AdministrationHTTPServer
from ohana_agent.api.service import AdministrationService
from ohana_agent.infrastructure.repository import InfrastructureConfigurationRepository
from ohana_agent.configuration.power_plug import PowerPlugPluginConfig
from ohana_agent.jobs.power_plug import PowerPlugController
from ohana_agent.jobs.repository import DistributedJobRepository
from ohana_agent.jobs.wake_on_lan import WakeOnLanSender
from ohana_agent.plugins.power_plug.plugin import PowerPlugPlugin
from ohana_katsuyu.handlers import KatsuyuWorkspace, SystemHealthHandler
from ohana_katsuyu.power import ShutdownVeto
from ohana_katsuyu.worker import AgentClient, KatsuyuWorker

from scenarios._support import SandboxClock

WORKER = "katsuyu-sandbox"
MAC = "AA:BB:CC:DD:EE:FF"
ADMIN_TOKEN = "tsunade-sandbox"
WORKER_TOKEN = "katsuyu-sandbox-secret"
HA_TOKEN = "ha-plug-sandbox-token"
SWITCH = "switch.shellyplugsg3_80b54e297538"
POWER = "sensor.shellyplugsg3_80b54e297538_power"
INFRASTRUCTURE_YAML = """\
infrastructure:
  id: ohana-sandbox
  name: Ohana Sandbox
  environment: production
nodes: []
services: []
"""


class FakeHomeAssistant:
    """The two Home Assistant endpoints the plug uses, with a plug behind them."""

    def __init__(self) -> None:
        self.switch = "off"
        self.watts = 0.0
        self.down = False
        self.commands: list[tuple[str, str, str]] = []  # service, entity, auth
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_: object) -> None:
                return

            def _answer(self, status: int, body: object) -> None:
                raw = json.dumps(body).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def _authorised(self) -> bool:
                return self.headers.get("Authorization") == f"Bearer {HA_TOKEN}"

            def do_GET(self) -> None:  # noqa: N802
                if owner.down:
                    return self._answer(500, {"message": "down"})
                if not self._authorised():
                    return self._answer(401, {"message": "unauthorized"})
                entity = self.path.rsplit("/", 1)[-1]
                if entity == SWITCH:
                    return self._answer(200, {"state": owner.switch})
                if entity == POWER:
                    return self._answer(200, {"state": str(owner.watts)})
                return self._answer(404, {"message": "unknown"})

            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length) or b"{}")
                if owner.down:
                    return self._answer(500, {"message": "down"})
                if not self._authorised():
                    return self._answer(401, {"message": "unauthorized"})
                service = self.path.rsplit("/", 1)[-1]
                owner.commands.append(
                    (service, body.get("entity_id", ""), self.path)
                )
                if service in {"turn_on", "turn_off"}:
                    owner.switch = "on" if service == "turn_on" else "off"
                return self._answer(200, [])

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self._server.server_address[1]
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)


class _MagicPacketListener:
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


def _events(jobs: DistributedJobRepository) -> list:
    return list(reversed(jobs.list_workers().workers[0].power_events))


def _kinds(jobs: DistributedJobRepository) -> list[str]:
    return [event.kind.value for event in _events(jobs)]


def _queue(jobs: DistributedJobRepository, clock: SandboxClock, number: int) -> None:
    jobs.create(
        {
            "protocol_version": 1,
            "job_id": f"77777777-7777-4777-8777-{number:012d}",
            "type": "system.health",
            "created_at": clock.current.isoformat(),
            "parameters": {},
            "timeout": 6 * 3600,
        }
    )


def run() -> dict:
    checks: list[tuple[str, bool]] = []
    details: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-plug-") as tmp:
        root = Path(tmp)
        (root / "infrastructure.yaml").write_text(INFRASTRUCTURE_YAML, encoding="utf-8")
        clock = SandboxClock()
        jobs = DistributedJobRepository(root / "jobs.db", clock=clock)
        home_assistant = FakeHomeAssistant()
        listener = _MagicPacketListener()
        wakes: list[str] = []

        def send(mac: str) -> None:
            wakes.append(mac)
            WakeOnLanSender(
                mac_address=mac,
                broadcast_address="127.0.0.1",
                port=listener.port,
                burst_count=3,
                burst_interval_seconds=0.01,
            ).send()

        # The real plugin, with the configuration an owner saves from Vision.
        plug_configuration = PowerPlugPluginConfig(
            enabled=True,
            home_assistant_url=f"http://127.0.0.1:{home_assistant.port}",
            access_token=HA_TOKEN,
            switch_entity_id=SWITCH,
            power_entity_id=POWER,
            boot_delay_seconds=15,
            shutdown_grace_seconds=300,
            idle_watts=5.0,
            idle_confirm_seconds=30,
            poll_seconds=15,
        )
        plugin = PowerPlugPlugin(config=plug_configuration)
        controller = PowerPlugController(plugin, jobs, policy=plugin.policy)
        service = AdministrationService(
            infrastructure_repository=InfrastructureConfigurationRepository(
                root / "infrastructure.yaml"
            ),
            job_repository=jobs,
            wake_enabled=True,
            wake_sender=send,
            wake_minimum_interval_seconds=0,
            wake_worker_id=WORKER,
            power_plug=controller,
        )
        administration = AdministrationHTTPServer(
            service=service, token=ADMIN_TOKEN, worker_token=WORKER_TOKEN, port=0
        )
        administration.start()
        try:
            host, port = administration.address
            shutdowns: list[str] = []
            veto: list[ShutdownVeto | None] = [None]

            def make_worker() -> KatsuyuWorker:
                return KatsuyuWorker(
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

            def tick(seconds: int, count: int, watts: Any = None) -> None:
                for _ in range(count):
                    clock.advance(seconds=seconds)
                    if callable(watts):
                        home_assistant.watts = watts()
                    service.tick_power_plug(clock.current)

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
            worker = make_worker()

            # --- Cycle 1: unplugged PC, full cycle, plug cut at the end -----
            clock.advance(minutes=30)
            _queue(jobs, clock, 1)
            woke = service._wake_compatible_worker("system.health")  # noqa: SLF001
            time.sleep(0.3)
            held = (list(wakes), len(listener.packets))
            powered_at = clock.current
            checks += [
                (
                    "prise éteinte : allumée avant le réveil, commande authentifiée "
                    "sur la bonne entité",
                    woke
                    and home_assistant.switch == "on"
                    and home_assistant.commands
                    == [("turn_on", SWITCH, "/api/services/switch/turn_on")],
                ),
                (
                    "aucun paquet tant que le PC n'a pas eu 15 s de courant",
                    held == ([], 0),
                ),
            ]
            clock.advance(seconds=16)
            service.dispatch_due_wake_requests()
            time.sleep(0.3)
            checks.append(
                (
                    "15 s après l'allumage : paquets magiques réels reçus (3), "
                    "une seule fois",
                    len(wakes) == 1 and len(listener.packets) == 3,
                )
            )
            clock.advance(seconds=45)
            worker.register()
            processed = worker.run_once()
            clock.advance(seconds=5)
            worker.run_once()  # idle: shutdown granted
            shutdown_at = clock.current
            checks.append(
                (
                    "cycle complet journalisé, prise allumée avant le réveil",
                    _kinds(jobs)
                    == [
                        "plug_on",
                        "wake_sent",
                        "worker_online",
                        "shutdown_granted",
                        "shutdown_started",
                    ]
                    and processed
                    and shutdowns == ["shutdown"],
                )
            )
            wake_detail = _events(jobs)[1].detail
            checks.append(
                (
                    "le réveil journalise la prise et le délai avant le paquet",
                    wake_detail.get("plug") == "turned_on"
                    and wake_detail.get("wol_delay_seconds") == 15,
                )
            )

            # Windows is shutting down: the load stays high for 90 s.
            tick(
                20,
                5,
                lambda: (
                    35.0
                    if (clock.current - shutdown_at).total_seconds() < 90
                    else 0.6
                ),
            )
            still_on = home_assistant.switch == "on"
            tick(
                20,
                10,
                lambda: (
                    35.0
                    if (clock.current - shutdown_at).total_seconds() < 90
                    else 0.6
                ),
            )
            newest = jobs.list_workers().workers[0].power_events[0]
            checks += [
                (
                    "PC encore en train de s'éteindre (35 W) : la prise reste allumée",
                    still_on,
                ),
                (
                    "consommation tombée à 0,6 W pendant 30 s : prise coupée",
                    home_assistant.switch == "off"
                    and newest.kind.value == "plug_off"
                    and newest.detail["reason"] == "shutdown_started"
                    and newest.detail["watts"] == 0.6
                    and newest.detail["idle_seconds"] >= 30,
                ),
                (
                    "prise coupée après l'arrêt, jamais avant",
                    (newest.occurred_at - shutdown_at).total_seconds() >= 120
                    and controller._store.plug_turned_on_at() is None,  # noqa: SLF001
                ),
            ]
            commands_after_cut = len(home_assistant.commands)
            tick(20, 10)
            checks.append(
                (
                    "coupée une seule fois : plus aucune commande ensuite",
                    len(home_assistant.commands) == commands_after_cut,
                )
            )

            # --- Cycle 2: a session keeps the PC on, the plug stays on -------
            shutdowns.clear()
            veto[0] = ShutdownVeto("interactive_session", 1)
            worker = make_worker()
            clock.advance(days=1)
            _queue(jobs, clock, 2)
            service._wake_compatible_worker("system.health")  # noqa: SLF001
            clock.advance(seconds=16)
            service.dispatch_due_wake_requests()
            clock.advance(seconds=40)
            worker.register()
            worker.run_once()
            clock.advance(seconds=5)
            worker.run_once()  # granted, vetoed by the session
            home_assistant.watts = 60.0
            tick(60, 10)  # the worker no longer polls, the PC is in use
            kept_on = home_assistant.switch == "on" and shutdowns == []
            home_assistant.watts = 0.5  # the user shuts it down by hand
            tick(20, 8)
            last = jobs.list_workers().workers[0].power_events[0]
            checks += [
                (
                    "session ouverte (veto) : prise gardée allumée tant que le PC consomme",
                    kept_on,
                ),
                (
                    "PC éteint à la main ensuite : prise coupée, raison journalisée",
                    home_assistant.switch == "off"
                    and last.kind.value == "plug_off"
                    and last.detail["reason"] == "worker_offline",
                ),
            ]

            # --- Cycle 3: Home Assistant down, the wake still goes out -------
            veto[0] = None
            clock.advance(days=1)
            _queue(jobs, clock, 3)
            home_assistant.down = True
            commands_before = len(home_assistant.commands)
            wakes_before = len(wakes)
            service._wake_compatible_worker("system.health")  # noqa: SLF001
            kinds = _kinds(jobs)[-2:]
            sent = jobs.list_workers().workers[0].power_events[0]
            checks += [
                (
                    "Home Assistant injoignable : le réveil part quand même, sans délai",
                    len(wakes) == wakes_before + 1
                    and kinds == ["plug_failed", "wake_sent"]
                    and sent.detail["plug"] == "unreadable",
                ),
                (
                    "aucune commande n'atteint la prise pendant la panne",
                    len(home_assistant.commands) == commands_before,
                ),
            ]
            for _ in range(3):  # nobody answers: retries, then abandonment
                clock.advance(seconds=181)
                service.dispatch_due_wake_requests()
                clock.advance(seconds=600)
                service.dispatch_due_wake_requests()
            home_assistant.down = False
            tick(30, 20)
            checks.append(
                (
                    "réveil abandonné sans prise allumée par Ohana : prise laissée telle quelle",
                    "wake_abandoned" in _kinds(jobs)
                    and len(home_assistant.commands) == commands_before
                    and home_assistant.switch == "off",
                )
            )
            # --- The owner disables the plugin in Vision: live, no restart ----
            plugin.reconfigure(PowerPlugPluginConfig())
            clock.advance(days=1)
            _queue(jobs, clock, 4)
            wakes_before = len(wakes)
            service._wake_compatible_worker("system.health")  # noqa: SLF001
            newest_event = jobs.list_workers().workers[0].power_events[0]
            checks.append(
                (
                    "plugin désactivé dans Vision : réveil comme avant la prise, "
                    "aucune commande, rien dans le journal de la prise",
                    len(wakes) == wakes_before + 1
                    and len(home_assistant.commands) == commands_before
                    and newest_event.kind.value == "wake_sent"
                    and "plug" not in newest_event.detail,
                )
            )
            details["cycle"] = " → ".join(_kinds(jobs)[:5])
            details["prise"] = (
                f"allumée {powered_at:%H:%M:%S}, coupée "
                f"{newest.occurred_at:%H:%M:%S} (arrêt {shutdown_at:%H:%M:%S})"
            )
        finally:
            listener.close()
            administration.stop()
            jobs.close()
            home_assistant.close()
    details["portée"] = (
        "Agent HTTP, worker Katsuyu, client Home Assistant (HTTP) et émetteur "
        "Wake-on-LAN réels ; Home Assistant, arrêt Windows, sessions et horloge simulés"
    )
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
