"""Shikamaru verifies a repair right after it runs, not at the next cycle.

Real production bootstrap: scheduler, NTP plugin, Tsunade observation handler,
administration service and chrony executor. The NTP service is a local UDP
responder, observed hourly as on Konoha, and the chrony executor writes its
request to a temporary file watched by nothing. Time is a fake clock, so the
hourly cycle never comes during the scenario: only the probes requested by
the repair can verify it.
"""

from __future__ import annotations

import os
import socket
import struct
import tempfile
import threading
import time
from datetime import timedelta
from pathlib import Path
from typing import Any
from unittest.mock import patch
from uuid import UUID

import ohana_agent

from ohana_agent.runtime.bootstrap import build_production_agent
from ohana_agent.scheduler import FakeClock
from ohana_agent.tsunade.expertise import TsunadeExpertiseService
from ohana_agent.tsunade.local_time import paris_now
from ohana_agent.tsunade.repair_catalog import repair_spec

NTP_EPOCH_DELTA = 2_208_988_800


class FakeVisionClient:
    """Discard Vision exports."""

    def send_observation(self, payload: dict[str, Any]) -> None:
        del payload

    def send_infrastructure(self, payload: dict[str, Any]) -> None:
        del payload


class LocalNTP:
    """Answer SNTP requests only while ``running`` is set, like chrony."""

    def __init__(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("127.0.0.1", 0))
        self.socket.settimeout(0.2)
        self.port = self.socket.getsockname()[1]
        self.running = threading.Event()
        self.requests = 0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._serve, daemon=True)

    def __enter__(self) -> LocalNTP:
        self._thread.start()
        return self

    def __exit__(self, *_exc: object) -> None:
        self._stop.set()
        self._thread.join(timeout=2)
        self.socket.close()

    def _serve(self) -> None:
        while not self._stop.is_set():
            try:
                request, client = self.socket.recvfrom(512)
            except (TimeoutError, OSError):
                continue
            self.requests += 1
            if not self.running.is_set() or len(request) < 48:
                continue
            now = time.time() + NTP_EPOCH_DELTA
            seconds, fraction = int(now), int((now % 1) * (1 << 32))
            response = bytearray(48)
            response[0] = (0 << 6) | (4 << 3) | 4  # LI 0, NTP v4, server.
            response[1] = 2
            response[24:32] = request[40:48]
            struct.pack_into("!IIII", response, 32, seconds, fraction, seconds, fraction)
            self.socket.sendto(bytes(response), client)


def _configuration(root: Path, ntp_port: int) -> dict[str, Path]:
    token = root / "management.token"
    token.write_text("management-secret\n", encoding="utf-8")
    path_unit = root / "ohana-chrony-restart.path"
    path_unit.write_text("[Path]\n", encoding="utf-8")
    request = root / "run" / "chrony-restart.request"
    application = root / "shikamaru.yaml"
    application.write_text(
        f"""\
version: 1
agent:
  name: Shikamaru
  environment: test
vision:
  enabled: true
  observation_url: http://127.0.0.1:8000/api/observations
  infrastructure_url: http://127.0.0.1:8000/api/infrastructure
administration:
  enabled: true
  token_file: {token.as_posix()}
  database_path: {(root / "control.db").as_posix()}
  dhcp:
    enabled: false
  ntp:
    restart_request_path: {request.as_posix()}
    restart_path_unit: {path_unit.as_posix()}
""",
        encoding="utf-8",
    )
    infrastructure = root / "infrastructure.yaml"
    infrastructure.write_text(
        f"""\
infrastructure:
  id: konoha
  name: Konoha
nodes:
  - id: infra-01
    name: INFRA-01
    endpoint:
      type: ip
      address: 127.0.0.1
services:
  - id: chrony
    name: NTP
    type: ntp
    node: infra-01
    port: {ntp_port}
    implementation: NTP
""",
        encoding="utf-8",
    )
    ntp = root / "ntp.yaml"
    ntp.write_text(
        """\
enabled: true
timeout: 0.5
retries: 0
interval_seconds: 3600
policy:
  maximum_offset_ms: 1000.0
  maximum_stratum: 15
""",
        encoding="utf-8",
    )
    return {
        "application": application,
        "infrastructure": infrastructure,
        "ntp": ntp,
        "request": request,
    }


def _wait(predicate, timeout: float = 3.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.05)
    return predicate()


def run() -> dict:
    agent_root = Path(ohana_agent.__file__).resolve().parents[2]
    started: list[UUID] = []
    checks: list[tuple[str, bool]] = []
    details: dict[str, object] = {}

    def record_start(self, incident_id, *, log_result=None) -> None:
        del self, log_result
        started.append(incident_id)

    with (
        tempfile.TemporaryDirectory(prefix="ohana-sandbox-verification-") as tmp,
        LocalNTP() as ntp,
    ):
        root = Path(tmp)
        paths = _configuration(root, ntp.port)
        clock = FakeClock(paris_now())
        previous_directory = Path.cwd()
        service = None
        try:
            os.chdir(agent_root)
            with patch.object(TsunadeExpertiseService, "start", new=record_start):
                agent = build_production_agent(
                    application_config_path=paths["application"],
                    infrastructure_config_path=paths["infrastructure"],
                    ntp_config_path=paths["ntp"],
                    vision_client=FakeVisionClient(),
                    clock=clock,
                )
                assert agent.administration_runtime is not None
                service = agent.administration_runtime.service
                incidents = service.incident_repository
                scheduler = agent.scheduler
                ntp_tasks = [
                    task for task in scheduler.list_tasks() if task.command == "ntp.query"
                ]
                scheduler.start()

                # chrony is stopped: the hourly cycle opens the incident.
                scheduler.tick()
                opened = _wait(lambda: bool(started))
                checks.append(
                    (
                        "panne chrony observée au cycle horaire, incident ouvert",
                        len(ntp_tasks) == 1 and opened,
                    )
                )
                if not opened:
                    return {"passed": False, "checks": checks, "details": details}
                incident_id = started[0]
                repair = incidents.propose_repair(
                    incident_id, repair_spec("restart_service", "chrony.service")
                )

                # The helper restarts chrony; the Agent executes the repair.
                ntp.running.set()
                requests_before = ntp.requests
                verifying = service.authorize_incident_repair(
                    str(incident_id),
                    {"repair_id": str(repair.repair_id), "source": "vision"},
                )
                checks.append(
                    (
                        "réparation autorisée et exécutée, vérification en attente",
                        verifying.status == "verifying" and paths["request"].is_file(),
                    )
                )

                clock.advance(timedelta(seconds=10))
                scheduler.tick()
                checks.append(
                    (
                        "aucune sonde avant la stabilisation du service",
                        ntp.requests == requests_before
                        and incidents.get_repair(repair.repair_id).status
                        == "verifying",
                    )
                )

                clock.advance(timedelta(seconds=10))
                scheduler.tick()
                verified = _wait(
                    lambda: incidents.get_repair(repair.repair_id).status
                    == "succeeded"
                )
                final = incidents.get(incident_id)
                checks.append(
                    (
                        "sonde 20 s après l'exécution : Shikamaru confirme sans "
                        "attendre le cycle horaire",
                        verified and ntp.requests == requests_before + 1,
                    )
                )
                checks.append(
                    ("incident chrony résolu", final.state == "resolved")
                )
                details = {
                    "réparation": final.repairs[0].status,
                    "résultat": final.repairs[0].result,
                    "requêtes NTP après exécution": ntp.requests - requests_before,
                }
        finally:
            os.chdir(previous_directory)
            if service is not None:
                if service.job_repository is not None:
                    service.job_repository.close()
                if service.incident_repository is not None:
                    service.incident_repository.close()

    return {
        "passed": all(passed for _, passed in checks),
        "checks": checks,
        "details": details,
    }
