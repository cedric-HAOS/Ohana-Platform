"""Phase 10: a backup is demonstrated restorable only by a declared restoration.

The four backup targets (HA-01, LINKY-01, ZWAVE-01, INFRA-01) report their
real ``backup.run`` observations through the event Tsunade's preventive monitor
subscribes to. The Agent service then answers Vision (detail) and Shizune
(essential): a target never restored is named, a failed restoration is urgent,
and a declared success leaves the list. Nothing is ever deduced, no incident or
repair is opened, and the evidence survives an Agent restart.
"""

from __future__ import annotations

import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from ohana_agent.api.service import AdministrationService
from ohana_agent.infrastructure.repository import InfrastructureConfigurationRepository
from ohana_agent.observation import ObservationStatus
from ohana_agent.observation.observation import Observation
from ohana_agent.tsunade.incidents import TsunadeIncidentRepository
from ohana_agent.tsunade.preventive import TsunadePreventiveMonitor

PARIS = ZoneInfo("Europe/Paris")
TARGETS = ("ha-01", "linky-01", "zwave-01", "infra-01")


def _open(root: Path):
    database = root / "control.db"
    incidents = TsunadeIncidentRepository(database)
    monitor = TsunadePreventiveMonitor(database)
    service = AdministrationService(
        infrastructure_repository=InfrastructureConfigurationRepository(
            root / "infrastructure.yaml"
        ),
        incident_repository=incidents,
        preventive_monitor=monitor,
        job_repository=None,
    )
    return incidents, monitor, service


def _backup(target: str, at: datetime, *, success: bool = True) -> SimpleNamespace:
    # The monitor consumes ObservationPublished events: ``event.observation``.
    return SimpleNamespace(
        observation=Observation(
            node=target,
            service=target,
            capability="backup.run",
            status=ObservationStatus.HEALTHY if success else ObservationStatus.UNHEALTHY,
            success=success,
            message="Sauvegarde",
            source="backup",
            timestamp=at,
        )
    )


def _tables(root: Path) -> dict[str, int]:
    connection = sqlite3.connect(root / "control.db")
    try:
        return {
            name: connection.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]  # noqa: S608
            for name in ("tsunade_incidents", "tsunade_repairs")
            if connection.execute(
                "SELECT 1 FROM sqlite_master WHERE name = ?", (name,)
            ).fetchone()
        }
    finally:
        connection.close()


def _check(summary: dict) -> dict:
    return next(item for item in summary["checks"] if item["id"] == "backup_restore")


def _states(service: AdministrationService) -> dict[str, str]:
    return {t["target"]: t["state"] for t in service.read_restore_tests()["targets"]}


def run() -> dict:
    checks: list[tuple[str, bool]] = []
    details: dict[str, str] = {}
    now = datetime.now(PARIS)
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-restore-") as tmp:
        root = Path(tmp)
        incidents, monitor, service = _open(root)
        try:
            empty = _check(service.read_preventive_summary())
            for index, target in enumerate(TARGETS):
                monitor.handle_observation(_backup(target, now - timedelta(hours=index + 3)))
            monitor.handle_observation(
                _backup("ha-01", now - timedelta(hours=1), success=False)
            )
            untested = service.read_preventive_summary()
            ha_posture = next(
                t for t in service.read_restore_tests()["targets"] if t["target"] == "ha-01"
            )
            essential = service.read_companion_summary()["preventive"]
            baseline = _tables(root)

            service.declare_restore_test(
                {
                    "target": "ha-01",
                    "outcome": "ok",
                    "tested_at": (now - timedelta(days=1)).isoformat(),
                    "reference": "essai sur une copie de HA-01",
                }
            )
            service.declare_restore_test(
                {
                    "target": "infra-01",
                    "outcome": "failed",
                    "note": "L'identité age de récupération était absente.",
                }
            )
            mixed = service.read_preventive_summary()
            mixed_states = _states(service)
            refused = []
            for payload in (
                {"target": "zwave-01", "outcome": "partial"},
                {"target": "zwave-01", "outcome": "ok", "tested_at": "hier"},
                {"target": "zwave-01", "outcome": "ok", "tested_at": (now + timedelta(days=2)).isoformat()},
            ):
                try:
                    service.declare_restore_test(payload)
                except ValueError:
                    refused.append(payload)
        finally:
            monitor.close()
            incidents.close()

        # The Agent restarts (deployment): the evidence is still there.
        incidents, monitor, service = _open(root)
        try:
            service.declare_restore_test(
                {"target": "infra-01", "outcome": "ok", "reference": "reprise après correctif"}
            )
            repaired = service.read_preventive_summary()
            restarted_states = _states(service)
            after = _tables(root)
        finally:
            monitor.close()
            incidents.close()

    titles = [item["title"] for item in untested["watch"] if item["rule"] == "backup_restore"]
    failed = next(i for i in mixed["watch"] if i["subject"] == "infra-01")
    checks += [
        (
            "sans sauvegarde observée, la règle n'a rien à juger",
            empty["state"] == "insufficient_data",
        ),
        (
            "quatre cibles sauvegardées, aucune restaurée : toutes nommées",
            sorted(titles)
            == sorted(f"{t.upper()} : sauvegarde jamais testée en restauration" for t in TARGETS),
        ),
        (
            "une sauvegarde échouée ne compte pas comme une sauvegarde",
            ha_posture["backup_successes"] == 1,
        ),
        (
            "Shizune reçoit l'essentiel : titres sans preuves",
            {w["title"] for w in essential["watch"]} >= set(titles)
            and "evidence" not in str(essential),
        ),
        (
            "une restauration réussie déclarée sort la cible de la liste",
            mixed_states["ha-01"] == "verified"
            and all(i["subject"] != "ha-01" for i in mixed["watch"]),
        ),
        (
            "une restauration échouée est urgente et cite la note",
            mixed_states["infra-01"] == "last_failed"
            and failed["urgent"] is True
            and "identité age" in failed["detail"]
            and mixed["conclusion"].startswith("Intervention à prévoir"),
        ),
        (
            "déclarations invalides refusées (note absente, date illisible ou future)",
            len(refused) == 3,
        ),
        (
            "les preuves survivent au redémarrage de l'Agent",
            restarted_states["ha-01"] == "verified",
        ),
        (
            "un nouveau test réussi lève l'alerte urgente",
            restarted_states["infra-01"] == "verified"
            and all(not i["urgent"] for i in repaired["watch"]),
        ),
        (
            "aucun incident ni réparation ouverts par la seule déclaration",
            after == baseline and repaired["automatic_actions"] is False,
        ),
    ]
    details["bilan"] = untested["text"].replace("\n", " / ")
    details["portée"] = (
        "Agent et SQLite locaux, observations backup.run par événement, "
        "sans Katsuyu, sans iCloud et sans restauration réelle"
    )
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }

