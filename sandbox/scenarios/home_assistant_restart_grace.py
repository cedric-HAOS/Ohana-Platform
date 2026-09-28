"""An entity Home Assistant loses while it restarts is not a critical fault.

HA-01 update, 28 September: during the restart the Home Assistant API
answered "Entity not found" for the SUN-01 power sensor, and Tsunade opened
a critical incident for five minutes although nothing was broken.

A local Home Assistant stand-in answers through real HTTP; the real telemetry
plugin, observation mappers and Tsunade incident repository do the rest. The
entity missing must be degraded first, critical only once the grace period
is over, and a value that stopped reporting stays critical at once.
"""

from __future__ import annotations

import json
import tempfile
import threading
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ohana_agent.observation import ObservationStatus
from ohana_agent.observation.infrastructure_observation_mapper import (
    InfrastructureObservationMapper,
)
from ohana_agent.observation.observer_result_mapper import ObserverResultMapper
from ohana_agent.plugins.home_assistant_telemetry import plugin as telemetry
from ohana_agent.plugins.home_assistant_telemetry.config import (
    HomeAssistantTelemetryConfig,
)
from ohana_agent.tsunade.incidents import TsunadeIncidentRepository

ENTITY = "sensor.sun_01_power"


class _HomeAssistant(BaseHTTPRequestHandler):
    mode = "missing"

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        if self.mode == "missing":
            self._reply(404, {"message": "Entity not found."})
            return
        reported = datetime.now(UTC) - (
            timedelta(hours=1) if self.mode == "stale" else timedelta(seconds=5)
        )
        self._reply(
            200,
            {
                "entity_id": ENTITY,
                "state": "10.5",
                "attributes": {"unit_of_measurement": "W"},
                "last_reported": reported.isoformat(),
            },
        )

    def _reply(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args) -> None:
        return None


def run() -> dict:
    checks = []
    details = {}
    server = ThreadingHTTPServer(("127.0.0.1", 0), _HomeAssistant)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    clock = [1000.0]
    # Agents before 1.38.1 have no grace period, hence no clock to replace.
    original_monotonic = getattr(telemetry, "monotonic", None)
    telemetry.monotonic = lambda: clock[0]
    try:
        with tempfile.TemporaryDirectory(prefix="ohana-sandbox-ha-restart-") as tmp:
            incidents = TsunadeIncidentRepository(Path(tmp) / "incidents.db")
            plugin = telemetry.HomeAssistantTelemetryPlugin(
                config=HomeAssistantTelemetryConfig(
                    home_assistant_url=f"http://127.0.0.1:{server.server_port}",
                    access_token="sandbox",
                    retries=0,
                )
            )

            def observe(mode: str):
                _HomeAssistant.mode = mode
                result = plugin.execute(
                    service_id="mesure-puissance",
                    service_name="Mesure Puissance",
                    node_id="sun-01",
                    primary_entity_id=ENTITY,
                    maximum_age_seconds=600,
                )
                update = ObserverResultMapper().map(
                    result, target_name="mesure-puissance"
                )
                observation = InfrastructureObservationMapper().map(
                    update,
                    node="sun-01",
                    service="mesure-puissance",
                    capability="home_assistant.telemetry.freshness",
                )
                return observation, incidents.process(observation)

            try:
                observation, incident = observe("missing")
                checks.append(
                    (
                        "entité introuvable pendant le redémarrage : incident dégradé",
                        observation.status is ObservationStatus.DEGRADED
                        and incident is not None
                        and incident.severity == "degraded",
                    )
                )
                clock[0] += 601
                observation, incident = observe("missing")
                checks.append(
                    (
                        "toujours introuvable après 10 minutes : incident critique",
                        observation.status is ObservationStatus.UNHEALTHY
                        and incident is not None
                        and incident.severity == "critical",
                    )
                )
                _observation, incident = observe("fresh")
                checks.append(
                    (
                        "valeur revenue : incident résolu",
                        incident is not None and incident.state == "resolved",
                    )
                )
                observation, incident = observe("stale")
                checks.append(
                    (
                        "valeur qui ne rapporte plus : critique immédiatement",
                        observation.status is ObservationStatus.UNHEALTHY
                        and incident is not None
                        and incident.severity == "critical",
                    )
                )
            finally:
                incidents.close()
    finally:
        if original_monotonic is None:
            del telemetry.monotonic
        else:
            telemetry.monotonic = original_monotonic
        server.shutdown()
    details["portée"] = (
        "Home Assistant simulé en HTTP ; plugin, mappers et incidents Tsunade réels"
    )
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
