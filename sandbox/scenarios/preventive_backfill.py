"""Phase 4, lot 3: missing days rebuilt by Katsuyu from Home Assistant.

The real Agent service queues trends.history_backfill, the real Katsuyu
handler reads a simulated Home Assistant WebSocket (entity registry and
hourly long-term statistics) through the Agent's job-bound descriptor, and
Tsunade stores one row per Paris day. Katsuyu absent: the job waits, the
simple checks still answer.
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from ohana_agent.api.service import AdministrationService
from ohana_agent.infrastructure.repository import InfrastructureConfigurationRepository
from ohana_agent.jobs.log_sources import LogSourceBroker
from ohana_agent.jobs.repository import DistributedJobRepository
from ohana_agent.observation import ObservationStatus
from ohana_agent.observation.observation import Observation
from ohana_agent.plugins.backup.config import BackupConfig, BackupTarget
from ohana_agent.tsunade.incidents import TsunadeIncidentRepository
from ohana_agent.tsunade.preventive import TsunadePreventiveMonitor
from ohana_katsuyu.handlers import HandlerContext, TrendsHistoryBackfillHandler

PARIS = ZoneInfo("Europe/Paris")
WORKER = "katsuyu-sandbox"
ENTITY = "sensor.ohana_host_utilisation_disque_racine"


class HomeAssistant:
    """Entity registry and hourly statistics, like HA-01 answers them."""

    def __init__(self, daily_maximum: dict[str, float]) -> None:
        self.daily_maximum = daily_maximum
        self.outbox = [{"type": "auth_required"}]
        self.requests: list[str] = []

    def __call__(self, _url, **_options):
        return self

    def recv(self):
        return json.dumps(self.outbox.pop(0))

    def send(self, raw):
        message = json.loads(raw)
        self.requests.append(message["type"])
        if message["type"] == "auth":
            ok = message["access_token"] == "ha-sandbox-token"
            self.outbox.append({"type": "auth_ok" if ok else "auth_invalid"})
        elif message["type"] == "config/entity_registry/list":
            self.outbox.append(
                {
                    "id": message["id"],
                    "success": True,
                    "result": [
                        {
                            "entity_id": ENTITY,
                            "platform": "mqtt",
                            "unique_id": "ohana_host_disk_usage",
                        }
                    ],
                }
            )
        elif message["type"] == "recorder/statistics_during_period":
            start = datetime.fromisoformat(message["start_time"])
            end = datetime.fromisoformat(message["end_time"])
            rows = []
            at = start
            while at < end:
                peak = self.daily_maximum.get(at.astimezone(PARIS).date().isoformat())
                if peak is not None:
                    value = peak if at.astimezone(PARIS).hour == 14 else peak - 0.6
                    rows.append(
                        {
                            "start": at.astimezone(UTC).timestamp() * 1000,
                            "min": value - 0.1,
                            "max": value,
                            "mean": value - 0.05,
                        }
                    )
                at += timedelta(hours=1)
            self.outbox.append(
                {"id": message["id"], "success": True, "result": {ENTITY: rows}}
            )

    def close(self):
        pass


def _konoha(root: Path, now):
    jobs = DistributedJobRepository(root / "jobs.db", clock=lambda: now[0])
    incidents = TsunadeIncidentRepository(root / "control.db")
    monitor = TsunadePreventiveMonitor(root / "control.db")
    service = AdministrationService(
        infrastructure_repository=InfrastructureConfigurationRepository(
            root / "infrastructure.yaml"
        ),
        job_repository=jobs,
        incident_repository=incidents,
        preventive_monitor=monitor,
        log_source_broker=LogSourceBroker(
            BackupConfig(
                targets=(
                    BackupTarget(
                        id="ha-01",
                        label="HA-01",
                        url="https://ha-01.ohana.lan:8123",
                        schedule="0 3 * * *",
                        token="ha-sandbox-token",
                        timeout=30,
                    ),
                )
            ),
            jobs,
        ),
        agent_node_id="infra-01",
    )
    return service, jobs, incidents, monitor


def _live(monitor, at, disk):
    monitor.record_host_health(
        Observation(
            node="infra-01",
            service="ohana-host",
            capability="host.health",
            status=ObservationStatus.HEALTHY,
            success=True,
            message="Host healthy",
            source="host-health",
            timestamp=at,
            metadata={"host_health": {"disk_percent": disk}},
        )
    )
    monitor.flush()


def _tables(root: Path) -> dict[str, int]:
    connection = sqlite3.connect(root / "control.db")
    try:
        return {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # noqa: S608
            for table in ("tsunade_incidents", "tsunade_repairs", "tsunade_user_requests")
        }
    finally:
        connection.close()


def _disk(summary):
    check = next(c for c in summary["checks"] if c["id"] == "disk_growth")
    return check, (check["nodes"] or [{}])[0]


def run() -> dict:
    checks: list[tuple[str, bool]] = []
    details: dict[str, str] = {}
    start = datetime.now(PARIS)
    now = [start]
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-backfill-") as tmp:
        root = Path(tmp)
        service, jobs, incidents, monitor = _konoha(root, now)
        try:
            # Deployed yesterday: the Agent measured yesterday and today only.
            _live(monitor, start - timedelta(days=1), 73.9)
            _live(monitor, start, 74.8)
            before = service.read_preventive_summary()
            check, node = _disk(before)
            checks.append(
                (
                    "2 jours mesurés : « historique insuffisant », rien de deviné",
                    check["state"] == "insufficient_data" and node["days"] == 2,
                )
            )

            # Katsuyu is away: the scheduled check queues one job, which waits.
            job = service.request_preventive_backfill(now=now[0], automatic=True)
            again = service.request_preventive_backfill(now=now[0], automatic=True)
            waiting = service.read_preventive_summary()
            checks += [
                (
                    "jours manquants : un seul rattrapage demandé à Katsuyu",
                    job is not None
                    and job.type == "trends.history_backfill"
                    and again is None,
                ),
                (
                    "Katsuyu absent : les contrôles simples répondent toujours",
                    waiting["conclusion"] == "Aucune intervention nécessaire."
                    and waiting["backfill"]["job"]["status"]
                    in {"QUEUED", "WAITING_WORKER", "CREATED"},
                ),
            ]

            # Katsuyu wakes up and runs the real handler.
            jobs.register_worker(
                {
                    "worker_id": WORKER,
                    "platform": "Windows",
                    "worker_version": "sandbox",
                    "capabilities": ["trends.history_backfill"],
                }
            )
            claim = service.next_worker_job(
                {"worker_id": WORKER, "supported_types": ["trends.history_backfill"]}
            ).job
            history = {
                (start.date() - timedelta(days=offset)).isoformat(): value
                for offset, value in (
                    (6, 68.0), (5, 69.3), (4, 70.1), (3, 71.4), (2, 72.6),
                    # Home Assistant also has yesterday: the Agent's value wins.
                    (1, 10.0),
                )
            }
            home_assistant = HomeAssistant(history)
            handler = TrendsHistoryBackfillHandler(
                service.read_history_source, connect=home_assistant
            )
            result = handler.execute(
                claim.parameters,
                HandlerContext(
                    job_id=str(claim.job_id), worker_id=WORKER, attempt=claim.attempt
                ),
            )
            tables_before = _tables(root)
            service.complete_job(
                str(claim.job_id),
                {
                    "worker_id": WORKER,
                    "attempt": claim.attempt,
                    "status": "SUCCEEDED",
                    "result": result,
                },
            )
            after = service.read_preventive_summary()
            check, node = _disk(after)
            checks += [
                (
                    "Katsuyu lit le registre puis les statistiques horaires de HA",
                    home_assistant.requests
                    == [
                        "auth",
                        "config/entity_registry/list",
                        "recorder/statistics_during_period",
                    ]
                    and result["rows_read"] == 6 * 24
                    and len(result["days"]) == 6,
                ),
                (
                    "5 jours reconstruits ; les jours mesurés par l'Agent sont gardés",
                    node.get("rebuilt_days") == 5
                    and node.get("days") == 7
                    and node.get("latest_percent") == 74.8,
                ),
                (
                    "avec l'historique rattrapé, la croissance du disque est signalée",
                    [item["rule"] for item in after["watch"]] == ["disk_growth"],
                ),
                (
                    "le rattrapage ne crée ni incident, ni réparation, ni demande",
                    _tables(root) == tables_before
                    and after["automatic_actions"] is False,
                ),
            ]

            # Nothing is missing any more: no new request, even a day later.
            now[0] = start + timedelta(hours=25)
            _live(monitor, now[0], 75.9)
            checks.append(
                (
                    "plus aucun jour manquant : aucune nouvelle demande",
                    service.request_preventive_backfill(now=now[0], automatic=True)
                    is None,
                )
            )
            details["rattrapage"] = (
                f"{len(result['days'])} jours lus ({result['entity_id']}), "
                f"{node.get('rebuilt_days')} retenus"
            )
            details["synthèse"] = after["text"].replace("\n", " / ")
        finally:
            monitor.close()
            incidents.close()
            jobs.close()
    details["portée"] = (
        "Agent et Katsuyu locaux (vrai gestionnaire), Home Assistant simulé"
    )
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
