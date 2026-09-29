"""Phase 4 hardening: new trends, adaptive windows, seasonality, fewer alerts.

Four weeks of history are replayed into the real Tsunade preventive monitor
of the Agent: memory, DNS response times with a busy-weekend pattern, the
daily Katsuyu log checks kept in the real job database, and hourly Home
Assistant samples read over HTTP by the real sampler (with one restart where
every entity is unavailable). The real incident repository and the
administration service provide the open incidents and the mutes.
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
from contextlib import closing
import threading
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo

from ohana_agent.api.service import AdministrationService
from ohana_agent.infrastructure.repository import InfrastructureConfigurationRepository
from ohana_agent.jobs.repository import DistributedJobRepository
from ohana_agent.observation.observation import Observation
from ohana_agent.observation.observation_status import ObservationStatus
from ohana_agent.tsunade.home_assistant_availability import (
    HomeAssistantAvailabilitySampler,
)
from ohana_agent.tsunade.incidents import TsunadeIncidentRepository
from ohana_agent.tsunade.preventive import TsunadePreventiveMonitor

PARIS = ZoneInfo("Europe/Paris")
NOW = datetime.now(PARIS).replace(hour=12, minute=0, second=0, microsecond=0)
DAYS = 28
SIGNATURE = "<timestamp> error (mainthread) [tapo_control] camera timed out"
NEWLY_UNAVAILABLE = [
    "binary_sensor.tapo_c200_person",
    "camera.tapo_c200",
    "select.tapo_c200_night_vision",
    "sensor.tapo_c200_signal",
    "switch.tapo_c200_privacy",
]


class _HomeAssistant(BaseHTTPRequestHandler):
    entities: list[dict] = []

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        body = json.dumps(self.entities).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args) -> None:
        return None


def _host(at: datetime, memory: float) -> Observation:
    return Observation(
        node="infra-01",
        service="ohana-host",
        capability="host.health",
        status=ObservationStatus.HEALTHY,
        success=True,
        message="Host healthy",
        source="host-health",
        timestamp=at,
        metadata={"host_health": {"memory_percent": memory, "swap_percent": 3.0}},
    )


def _dns(at: datetime, latency: float, *, healthy: bool = True) -> Observation:
    return Observation(
        node="infra-01",
        service="dns-secondaire",
        capability="dns.resolve",
        status=ObservationStatus.HEALTHY if healthy else ObservationStatus.UNHEALTHY,
        success=healthy,
        message="DNS",
        source="dns",
        timestamp=at,
        latency_ms=latency,
    )


def _entities(unavailable: list[str], total: int = 400) -> list[dict]:
    rows = [{"entity_id": name, "state": "unavailable"} for name in unavailable]
    rows += [
        {"entity_id": f"sensor.ok_{index}", "state": "1"}
        for index in range(total - len(rows))
    ]
    return rows


def run() -> dict:
    checks: list[tuple[str, bool]] = []
    details: dict[str, object] = {}
    server = ThreadingHTTPServer(("127.0.0.1", 0), _HomeAssistant)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-drifts-") as tmp:
        database = Path(tmp) / "distributed-jobs.db"
        jobs = DistributedJobRepository(database, clock=lambda: NOW)
        incidents = TsunadeIncidentRepository(database)
        monitor = TsunadePreventiveMonitor(database)
        recorded: list[datetime] = []
        sampler = HomeAssistantAvailabilitySampler(
            url=f"http://127.0.0.1:{server.server_port}",
            token=lambda: "sandbox",
            record_metric=lambda node, metric, value, _at: monitor.record_metric(
                node, metric, value, recorded[-1]
            ),
            record_snapshot=lambda node, kind, _at, detail: monitor.record_snapshot(
                node, kind, recorded[-1], detail
            ),
        )
        try:
            for offset in range(DAYS):
                day = NOW - timedelta(days=DAYS - 1 - offset)
                recent = offset >= DAYS - 7
                # Memory: 45 % for three weeks, then 63 % every day.
                monitor.record_host_health(_host(day, 63.0 if recent else 45.0))
                # DNS: always slow on weekends, the same last week: seasonal.
                slow = day.weekday() >= 5
                monitor.record_observation(_dns(day, 120.0 if slow else 18.0))
                monitor.record_observation(_dns(day, 9000.0, healthy=False))
                # Home Assistant: a restart (all unavailable) then the usual.
                _HomeAssistant.entities = _entities(
                    [f"sensor.item_{index}" for index in range(400)]
                )
                recorded.append(day)
                sampler.sample()
                usual = ["sensor.old_plug"]
                if recent:
                    usual += NEWLY_UNAVAILABLE
                _HomeAssistant.entities = _entities(usual)
                recorded.append(day + timedelta(hours=1))
                sampler.sample()
                # Katsuyu's daily log check, kept in the real job database.
                occurrences = 180 if recent else 12
                with closing(sqlite3.connect(database)) as connection, connection:
                    connection.execute(
                        """INSERT INTO distributed_jobs (job_id, protocol_version,
                        type, created_at, parameters_json, timeout_seconds, status,
                        finished_at, result_json, request_sha256, updated_at)
                        VALUES (?, 1, 'logs.health_check', ?, '{}', 600, 'SUCCEEDED',
                        ?, ?, '', ?)""",
                        (
                            f"sandbox-log-{offset}",
                            day.isoformat(),
                            day.isoformat(),
                            json.dumps(
                                {
                                    "sources": [
                                        {
                                            "source": "ha-01",
                                            "truncated": False,
                                            "findings": [
                                                {
                                                    "source": "ha-01",
                                                    "signature": SIGNATURE,
                                                    "occurrences": occurrences,
                                                }
                                            ],
                                        }
                                    ]
                                }
                            ),
                            day.isoformat(),
                        ),
                    )
            summary = monitor.summary(now=NOW)
            rules = {item["rule"]: item for item in summary["watch"]}
            by_id = {check["id"]: check for check in summary["checks"]}
            details["à surveiller"] = " ; ".join(i["title"] for i in summary["watch"])
            checks += [
                (
                    "mémoire 45 % → 63 % sur 7 jours : dérive signalée, preuve jointe",
                    "memory_growth" in rules
                    and rules["memory_growth"]["evidence"]["baseline_days"] >= 7
                    and rules["memory_growth"]["evidence"]["above"],
                ),
                (
                    "DNS lent chaque week-end : saisonnalité hebdomadaire, pas de dérive",
                    "response_time" not in rules
                    and any(
                        "même jour de la semaine" in node["summary"]
                        for node in by_id["response_time"]["nodes"]
                    ),
                ),
                (
                    "anomalie Tapo 12 → 180 par jour dans les contrôles Katsuyu : "
                    "signalée",
                    "log_errors_growth" in rules
                    and SIGNATURE[:40] in rules["log_errors_growth"]["title"],
                ),
                (
                    "Home Assistant : redémarrage ignoré, entités nouvellement "
                    "indisponibles nommées",
                    "ha_unavailable_entities" in rules
                    and rules["ha_unavailable_entities"]["evidence"]["newly_unavailable"]
                    == NEWLY_UNAVAILABLE,
                ),
                (
                    "dérives simultanées sur HA-01 : corrélation sans cause affirmée",
                    any(
                        item["equipment_id"] == "ha-01"
                        and "ne prouve aucune cause" in item["note"]
                        for item in summary["correlations"]
                    ),
                ),
            ]

            # Fewer useless alerts: mute through the administration service.
            service = AdministrationService(
                infrastructure_repository=InfrastructureConfigurationRepository(
                    Path(tmp) / "infrastructure.yaml"
                ),
                preventive_monitor=monitor,
            )
            service.mute_preventive(
                {
                    "rule": "log_errors_growth",
                    "subject": f"ha-01:{SIGNATURE}",
                    "days": 30,
                }
            )
            muted = monitor.summary(now=NOW)
            checks.append(
                (
                    "anomalie ignorée 30 jours : retirée de la liste, toujours visible",
                    not [i for i in muted["watch"] if i["rule"] == "log_errors_growth"]
                    and [i["rule"] for i in muted["muted"]] == ["log_errors_growth"],
                )
            )
            # A slower DNS already followed by an open incident is not a new alert.
            for offset in range(DAYS):
                day = NOW - timedelta(days=DAYS - 1 - offset)
                slow = offset >= DAYS - 7
                monitor.record_observation(
                    Observation(
                        node="infra-01",
                        service="dns-primaire",
                        capability="dns.resolve",
                        status=ObservationStatus.HEALTHY,
                        success=True,
                        message="DNS",
                        source="dns",
                        timestamp=day,
                        latency_ms=200.0 if slow else 15.0,
                    )
                )
            incidents.process(_dns(NOW, 9000.0, healthy=False))
            followed = monitor.summary(now=NOW)
            checks.append(
                (
                    "DNS plus lent pendant un incident DNS ouvert : suivi par "
                    "l'incident, pas une nouvelle alerte",
                    not [i for i in followed["watch"] if i["rule"] == "response_time"]
                    and any(
                        i["rule"] == "response_time"
                        for i in followed["followed_by_incident"]
                    ),
                )
            )
            checks.append(
                (
                    "aucune action automatique",
                    followed["automatic_actions"] is False,
                )
            )
        finally:
            server.shutdown()
            server.server_close()
            monitor.close()
            incidents.close()
            jobs.close()
    details["portée"] = (
        "moniteur préventif, échantillonneur HA, dépôts d'incidents et de jobs "
        "réels de l'Agent ; historique rejoué, Home Assistant simulé en HTTP"
    )
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
