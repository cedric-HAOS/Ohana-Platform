"""An Agent or Vision restart stays quiet, and host health speaks Paris time.

Phase 5 real trials, 29 September: stopping Vision for six minutes wrote one
"Unable to refresh infrastructure" warning every 10 s, and Vision's 50 s
start wrote 37 "Unable to deliver" warnings (every new observation retried
at once); Katsuyu counts each line. Restarting the Agent opened a critical
Linky incident for the minute teleinfo2mqtt needed to send its next frame,
the in-memory frame store being empty. host.health still dated its update
in UTC.

Real Agent components throughout: durable Vision client against a closed
port then a local stand-in, ProductionAgent refresh path, Téléinformation
plugin in direct mode with its real frame store, observation mappers and
the Tsunade incident repository, host health monitor.
"""

from __future__ import annotations

import logging
import socket
import tempfile
import threading
import time
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ohana_agent.observation import ObservationStatus
from ohana_agent.observation.exporters import (
    DurableVisionClient,
    HttpVisionClient,
    VisionClientError,
    VisionObservationOutbox,
)
from ohana_agent.observation.infrastructure_observation_mapper import (
    InfrastructureObservationMapper,
)
from ohana_agent.observation.observer_result_mapper import ObserverResultMapper
from ohana_agent.plugins.mqtt.host_health import HostHealthMonitor, HostMetrics
from ohana_agent.plugins.teleinformation import plugin as teleinformation
from ohana_agent.plugins.teleinformation.config import TeleinformationConfig
from ohana_agent.runtime.agent import ProductionAgent
from ohana_agent.scheduler import Scheduler
from ohana_agent.tsunade.incidents import TsunadeIncidentRepository

METER = "041964385922"


class _Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)

    def count(self, level: int, text: str) -> int:
        return sum(
            record.levelno == level and text in record.getMessage()
            for record in self.records
        )


class _Vision(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802 - http.server API
        self.rfile.read(int(self.headers.get("Content-Length") or 0))
        self.send_response(202)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b"{}")

    def log_message(self, *_args) -> None:
        return None


class _RefusingVision:
    """Infrastructure refresh against a Vision that is down."""

    def __init__(self) -> None:
        self.available = False

    def send_observation(self, payload: dict) -> None:
        del payload

    def send_infrastructure(self, payload: dict) -> None:
        del payload
        if not self.available:
            raise VisionClientError("Connection refused")


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _vision_client(port: int) -> HttpVisionClient:
    return HttpVisionClient(
        observation_url=f"http://127.0.0.1:{port}/api/observations",
        infrastructure_url=f"http://127.0.0.1:{port}/api/infrastructure",
        timeout_seconds=1.0,
    )


def _payload(index: int) -> dict:
    return {
        "observation_id": f"sandbox-quiet-{index}",
        "capability_id": "dns.resolve",
        "service_id": "dns-primary",
        "node_id": "infra-01",
        "status": "healthy",
        "observed_at": datetime.now(UTC).isoformat(),
        "metadata": {},
    }


def _delivery_checks(
    tmp: Path, capture: _Capture, details: dict
) -> list[tuple[str, bool]]:
    port = _free_port()
    outbox = VisionObservationOutbox(tmp / "outbox.db")
    client = DurableVisionClient(_vision_client(port), outbox, retry_seconds=0.5)
    client.start()
    try:
        # Vision starting: 20 observations in 1 s, nothing listens yet.
        for index in range(20):
            client.send_observation(_payload(index))
            time.sleep(0.05)
        # A refused local connection can take ~2 s on Windows: let several
        # retry periods pass before counting.
        deadline = time.monotonic() + 6
        while time.monotonic() < deadline and not capture.count(
            logging.DEBUG, "Unable to deliver observation"
        ):
            time.sleep(0.1)
        refused = capture.count(logging.WARNING, "Unable to deliver observation")
        details["essais refusés"] = refused + capture.count(
            logging.DEBUG, "Unable to deliver observation"
        )
        server = ThreadingHTTPServer(("127.0.0.1", port), _Vision)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            deadline = time.monotonic() + 5
            while client.pending_count and time.monotonic() < deadline:
                time.sleep(0.05)
            drained = client.pending_count == 0
        finally:
            server.shutdown()
            server.server_close()
    finally:
        client.stop()
    return [
        (
            "Vision indisponible : un seul avertissement de livraison par panne",
            refused == 1,
        ),
        ("Vision revenu : les 20 observations sont livrées", drained),
        (
            "rétablissement de la livraison journalisé une fois",
            capture.count(logging.INFO, "Delivery to Ohana-Vision restored") == 1,
        ),
    ]


def _refresh_checks(capture: _Capture) -> list[tuple[str, bool]]:
    vision = _RefusingVision()
    agent = ProductionAgent(
        scheduler=Scheduler(),
        vision_client=vision,  # type: ignore[arg-type]
        infrastructure_payload={"schema_version": 1},
    )
    # Six minutes of Vision down at one retry every 10 s.
    for _ in range(36):
        agent._refresh_infrastructure()
    vision.available = True
    agent._refresh_infrastructure()
    return [
        (
            "36 rafraîchissements refusés : un seul avertissement",
            capture.count(logging.WARNING, "Unable to refresh infrastructure") == 1,
        ),
        (
            "rafraîchissement rétabli journalisé une fois",
            capture.count(logging.INFO, "Infrastructure refresh in Ohana-Vision restored")
            == 1,
        ),
    ]


def _linky_checks(tmp: Path) -> list[tuple[str, bool]]:
    clock = [1000.0]
    original = getattr(teleinformation, "monotonic", None)
    teleinformation.monotonic = lambda: clock[0]
    incidents = TsunadeIncidentRepository(tmp / "incidents.db")
    try:
        plugin = teleinformation.TeleinformationPlugin(
            config=TeleinformationConfig(mode="direct_http", maximum_age_seconds=60),
        )

        def observe():
            result = plugin.execute(
                service_id="tic-linky",
                service_name="TIC Linky",
                node_id="linky-01",
                meter_id=METER,
                maximum_age_seconds=60,
            )
            update = ObserverResultMapper().map(result, target_name="tic-linky")
            observation = InfrastructureObservationMapper().map(
                update,
                node="linky-01",
                service="tic-linky",
                capability="teleinformation.freshness",
            )
            return observation, incidents.process(observation)

        clock[0] += 9
        first, first_incident = observe()
        clock[0] += 61
        late, late_incident = observe()
        plugin._check.frame_store.put(
            source="rpi-linky",
            meter_id=METER,
            frame={"SINSTS": {"raw": "948"}, "NTARF": {"raw": "02"}, "EASF02": "7913560"},
        )
        _fresh, fresh_incident = observe()
    finally:
        incidents.close()
        if original is None:
            del teleinformation.monotonic
        else:
            teleinformation.monotonic = original
    return [
        (
            "Agent démarré depuis 9 s sans trame Linky : inconnu, aucun incident",
            first.status is ObservationStatus.UNKNOWN and first_incident is None,
        ),
        (
            "toujours sans trame après la fenêtre de fraîcheur : incident critique",
            late.status is ObservationStatus.UNHEALTHY
            and late_incident is not None
            and late_incident.severity == "critical",
        ),
        (
            "trame reçue : incident résolu",
            fresh_incident is not None and fresh_incident.state == "resolved",
        ),
    ]


class _HostProbe:
    def collect(self) -> HostMetrics:
        return HostMetrics(
            hostname="infra-01",
            operating_system="Linux",
            kernel="6.18",
            cpu_count=4,
            cpu_percent=5.0,
            load_1m_per_cpu=0.2,
            memory_percent=50.0,
            memory_total_bytes=949_071_872,
            memory_available_bytes=433_274_880,
            swap_percent=5.0,
            swap_total_bytes=948_957_184,
            swap_used_bytes=49_229_824,
            disk_percent=24.5,
            disk_free_bytes=10_795_175_936,
            temperature_c=51.0,
            host_uptime_seconds=1_626_970,
            agent_uptime_seconds=47_330,
            agent_restarts=0,
            failed_systemd_units=(),
            inactive_systemd_units=(),
        )


def _host_health_checks() -> list[tuple[str, bool]]:
    snapshot = HostHealthMonitor(
        _HostProbe(),  # type: ignore[arg-type]
        utc_now=lambda: datetime(2026, 9, 29, 6, 30, tzinfo=UTC),
    ).collect()
    return [
        (
            "host.health date sa mise à jour en heure de Paris",
            snapshot.updated_at == "2026-09-29T08:30:00+02:00",
        )
    ]


def run() -> dict:
    capture = _Capture()
    loggers = [
        logging.getLogger("ohana_agent.observation.exporters.durable_vision_client"),
        logging.getLogger("ohana_agent.runtime.agent"),
    ]
    previous = [(log, log.level, log.propagate) for log in loggers]
    # The runner disables logging in compact mode; this scenario counts lines.
    previous_disable = logging.root.manager.disable
    logging.disable(logging.NOTSET)
    for log in loggers:
        log.addHandler(capture)
        log.setLevel(logging.DEBUG)
        log.propagate = False
    checks: list[tuple[str, bool]] = []
    details: dict = {}
    try:
        with tempfile.TemporaryDirectory(prefix="ohana-sandbox-quiet-") as tmp:
            checks += _delivery_checks(Path(tmp), capture, details)
            checks += _refresh_checks(capture)
            checks += _linky_checks(Path(tmp))
        checks += _host_health_checks()
    finally:
        logging.disable(previous_disable)
        for log, level, propagate in previous:
            log.removeHandler(capture)
            log.setLevel(level)
            log.propagate = propagate
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": {
            **details,
            "portée": (
                "client durable réel contre un port fermé puis un Vision local, "
                "rafraîchissement ProductionAgent, plugin Téléinformation direct "
                "et incidents Tsunade réels, moniteur de santé de l'hôte réel"
            ),
        },
    }
