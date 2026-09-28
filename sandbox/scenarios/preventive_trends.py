"""Phase 4, lot 1: a few explainable drifts, before they become incidents.

Seven days of INFRA-01 host health go through the real host health mapper
and the HostHealthObserved event into Tsunade's preventive monitor; network
interruptions go through the real incident repository. The Agent service
then answers Vision (detail) and Shizune (essential) without Katsuyu.
"""

from __future__ import annotations

import sqlite3
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from ohana_agent.api.service import AdministrationService
from ohana_agent.infrastructure.repository import InfrastructureConfigurationRepository
from ohana_agent.observation import ObservationStatus
from ohana_agent.observation.events import HostHealthObserved
from ohana_agent.observation.observation import Observation
from ohana_agent.plugins.mqtt.host_health import (
    HostHealthObservationMapper,
    HostHealthSnapshot,
)
from ohana_agent.tsunade.incidents import TsunadeIncidentRepository
from ohana_agent.tsunade.preventive import TsunadePreventiveMonitor

PARIS = ZoneInfo("Europe/Paris")
MAPPER = HostHealthObservationMapper()


@dataclass
class Konoha:
    root: Path
    incidents: TsunadeIncidentRepository
    monitor: TsunadePreventiveMonitor
    service: AdministrationService

    def close(self) -> None:
        self.monitor.close()
        self.incidents.close()


def _konoha(root: Path) -> Konoha:
    database = root / "control.db"
    incidents = TsunadeIncidentRepository(database)
    monitor = TsunadePreventiveMonitor(database)
    service = AdministrationService(
        infrastructure_repository=InfrastructureConfigurationRepository(
            root / "infrastructure.yaml"
        ),
        incident_repository=incidents,
        preventive_monitor=monitor,
        # Katsuyu is not configured at all: the rules must not need it.
        job_repository=None,
    )
    return Konoha(root, incidents, monitor, service)


def _snapshot(at: datetime, disk: float, boot: datetime, restarts: int):
    return HostHealthSnapshot(
        state="healthy",
        reasons=(),
        updated_at=at.isoformat(),
        hostname="infra-01",
        operating_system="Debian GNU/Linux 13",
        kernel="6.12",
        cpu_count=4,
        cpu_percent=12.0,
        load_1m_per_cpu=0.2,
        memory_percent=40.0,
        memory_total_bytes=4_000_000_000,
        memory_available_bytes=2_400_000_000,
        swap_percent=0.0,
        swap_total_bytes=0,
        swap_used_bytes=0,
        disk_percent=disk,
        disk_free_bytes=int((100 - disk) * 300_000_000),
        temperature_c=48.0,
        host_uptime_seconds=int((at - boot).total_seconds()),
        agent_uptime_seconds=3600,
        agent_restarts=restarts,
        failed_systemd_units=(),
        inactive_systemd_units=(),
    )


def _week(
    konoha: Konoha,
    now: datetime,
    daily_disk: list[float],
    boots: list[datetime],
    restarts_at: list[datetime] = (),
) -> None:
    """Hourly host health over the days given, through the real event path."""
    start = now - timedelta(days=len(daily_disk) - 1)
    at = start.replace(hour=0, minute=30)
    while at <= now:
        day = (at.date() - start.date()).days
        # Within a day the disk moves a little; the rule reads the maximum.
        disk = daily_disk[day] - (0.3 if at.hour < 12 else 0.0)
        boot = max(b for b in boots if b <= at)
        restarts = sum(1 for r in restarts_at if r <= at)
        observation = MAPPER.to_observation(_snapshot(at, disk, boot, restarts))
        konoha.monitor.handle(HostHealthObserved(observation))
        at += timedelta(hours=1)


def _interruption(konoha: Konoha, device: str, started: datetime, minutes: int):
    def observation(at: datetime, healthy: bool) -> Observation:
        return Observation(
            node="infra-01",
            service=device,
            capability="network.reachable",
            status=(
                ObservationStatus.HEALTHY if healthy else ObservationStatus.UNHEALTHY
            ),
            success=healthy,
            message="Équipement présent" if healthy else "Équipement absent",
            source="network",
            timestamp=at,
            metadata={"target_type": "device", "device_id": device},
        )

    konoha.incidents.process(observation(started - timedelta(minutes=5), True))
    konoha.incidents.process(observation(started, False))
    konoha.incidents.process(observation(started + timedelta(minutes=minutes), True))


def _tables(root: Path) -> dict[str, int]:
    connection = sqlite3.connect(root / "control.db")
    try:
        return {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # noqa: S608
            for table in (
                "tsunade_incidents",
                "tsunade_repairs",
                "tsunade_user_requests",
            )
        }
    finally:
        connection.close()


def _stable(checks, details, now) -> None:
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-preventive-") as tmp:
        konoha = _konoha(Path(tmp))
        try:
            # A normal week: logs grow slowly, one apt upgrade jumps once,
            # the host booted a month ago, one short Wi-Fi drop.
            _week(
                konoha,
                now,
                [71.0, 71.1, 71.2, 74.5, 74.6, 74.6, 74.7],
                [now - timedelta(days=30)],
            )
            _interruption(konoha, "esp-02", now - timedelta(days=2), 3)
            before = _tables(konoha.root)
            summary = konoha.service.read_preventive_summary()
            essential = konoha.service.read_companion_summary()["preventive"]
            checks += [
                (
                    "semaine normale : « Konoha est stable » et aucune intervention",
                    summary["status"] == "stable"
                    and summary["text"]
                    == "Konoha est stable.\n\nAucune intervention nécessaire.",
                ),
                (
                    "hausse lente et saut unique du disque : pas une anomalie",
                    next(c for c in summary["checks"] if c["id"] == "disk_growth")[
                        "state"
                    ]
                    == "ok",
                ),
                (
                    "Shizune reçoit la même conclusion, sans détail",
                    essential
                    == {
                        "status": "stable",
                        "watch": [],
                        "conclusion": "Aucune intervention nécessaire.",
                        "generated_at": essential["generated_at"],
                    },
                ),
                (
                    "la lecture ne crée ni incident, ni réparation, ni demande",
                    _tables(konoha.root) == before,
                ),
            ]
            details["semaine normale"] = summary["text"].replace("\n", " / ")
        finally:
            konoha.close()


def _drifts(checks, details, now) -> None:
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-preventive-") as tmp:
        root = Path(tmp)
        konoha = _konoha(root)
        try:
            _week(
                konoha,
                now,
                [68.0, 69.1, 70.3, 71.2, 72.6, 73.5, 74.7],
                [now - timedelta(days=30), now - timedelta(days=4, hours=3)],
                [now - timedelta(days=1, hours=5)],
            )
            for days, minutes in ((6, 4), (4, 11), (2, 2), (1, 7)):
                _interruption(
                    konoha, "zwave-01", now - timedelta(days=days, hours=2), minutes
                )
            before = _tables(root)
            first = konoha.service.read_preventive_summary()
        finally:
            konoha.close()

        # The Agent restarts (deployment): same data, same verdict.
        konoha = _konoha(root)
        try:
            second = konoha.service.read_preventive_summary()
            essential = konoha.service.read_companion_summary()["preventive"]
            after = _tables(root)
        finally:
            konoha.close()

    rules = {item["rule"]: item for item in first["watch"]}
    checks += [
        (
            "trois tendances détectées : disque, redémarrages, réseau",
            set(rules)
            == {"disk_growth", "repeated_reboots", "network_interruptions"},
        ),
        (
            "détection reproductible après redémarrage de l'Agent",
            [i["title"] for i in first["watch"]] == [i["title"] for i in second["watch"]],
        ),
        (
            "chaque règle est énoncée avec son seuil et ses preuves",
            all(check["rule"] for check in first["checks"])
            and rules["disk_growth"]["evidence"]["rises"] >= 3
            and len(rules["network_interruptions"]["evidence"]["interruptions"]) == 4,
        ),
        (
            "Shizune : l'essentiel, Vision : le détail",
            [w["title"] for w in essential["watch"]]
            == [i["title"] for i in second["watch"]]
            and "evidence" not in str(essential),
        ),
        (
            "aucune réparation déclenchée par la seule maintenance préventive",
            after == before and second["automatic_actions"] is False,
        ),
    ]
    details["dérives"] = first["text"].replace("\n", " / ")


def run() -> dict:
    checks: list[tuple[str, bool]] = []
    details: dict[str, str] = {}
    now = datetime.now(PARIS)
    _stable(checks, details, now)
    _drifts(checks, details, now)
    details["portée"] = (
        "Agent et SQLite locaux, santé hôte par HostHealthObserved, "
        "sans Katsuyu ni IA"
    )
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
