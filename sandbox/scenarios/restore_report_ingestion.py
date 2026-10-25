"""Phase 10: a restoration reported by Ohana-Installer reaches Tsunade.

The report is written by the real Installer module (``restore_report``) after a
simulated ``ohana restore`` and read by the real Agent monitor: a failed or
partial restoration is urgent, a complete one verifies INFRA-01, each report is
entered once and the files are never altered.
"""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from ohana_agent.api.service import AdministrationService
from ohana_agent.infrastructure.repository import InfrastructureConfigurationRepository
from ohana_agent.tsunade.incidents import TsunadeIncidentRepository
from ohana_agent.tsunade.preventive import TsunadePreventiveMonitor

PARIS = ZoneInfo("Europe/Paris")
INSTALLER_SOURCE = Path(__file__).resolve().parents[3] / "Ohana-Installer" / "src"


def _writer():
    if str(INSTALLER_SOURCE) not in sys.path:
        sys.path.insert(0, str(INSTALLER_SOURCE))
    from ohana_installer.restore_report import (  # noqa: PLC0415
        RestoreProgress,
        outcome_for_failure,
        write_report,
    )

    return RestoreProgress, outcome_for_failure, write_report


def run() -> dict:
    checks: list[tuple[str, bool]] = []
    details: dict[str, str] = {}
    RestoreProgress, outcome_for_failure, write_report = _writer()
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-restore-reports-") as tmp:
        root = Path(tmp)
        reports = root / "reports"
        incidents = TsunadeIncidentRepository(root / "control.db")
        monitor = TsunadePreventiveMonitor(
            root / "control.db", restore_report_directory=reports
        )
        service = AdministrationService(
            infrastructure_repository=InfrastructureConfigurationRepository(
                root / "infrastructure.yaml"
            ),
            incident_repository=incidents,
            preventive_monitor=monitor,
            job_repository=None,
        )
        try:
            nothing = service.read_restore_tests()["targets"]

            failed = RestoreProgress(mode="icloud", stage="configuration")
            failed.backup_id = "20261024T020000Z"
            failed_path = write_report(
                failed,
                outcome_for_failure(failed.stage),
                "Le service ohana-agent ne démarre pas. token=abc123",
                directory=reports,
            )
            monitor._reports_read_at = None  # noqa: SLF001 - skip the 60 s throttle.
            partial = service.read_restore_tests()["targets"][0]
            summary = service.read_preventive_summary()
            essential = service.read_companion_summary()["preventive"]
            before = failed_path.read_bytes()

            success = RestoreProgress(mode="icloud", stage="done")
            success.backup_id = "20261025T030000Z"
            write_report(success, "ok", "Restauration terminée.", directory=reports)
            monitor._reports_read_at = None  # noqa: SLF001
            verified = service.read_restore_tests()["targets"][0]
            monitor._reports_read_at = None  # noqa: SLF001
            again = service.read_restore_tests()["targets"][0]
            urgent_after = [
                i for i in service.read_preventive_summary()["watch"] if i["urgent"]
            ]
            untouched = failed_path.read_bytes() == before
        finally:
            monitor.close()
            incidents.close()

    item = next(i for i in summary["watch"] if i["rule"] == "backup_restore")
    checks += [
        ("aucun compte rendu : aucune cible", nothing == []),
        (
            "restauration partielle rapportée par l'Installer : enregistrée pour INFRA-01",
            partial["target"] == "infra-01"
            and partial["last_test"]["outcome"] == "partial"
            and partial["last_test"]["source"] == "installer"
            and partial["last_test"]["reference"] == "20261024T020000Z",
        ),
        (
            "urgente, avec l'étape atteinte, sans secret",
            item["urgent"] is True
            and "restauration des configurations" in item["detail"]
            and "abc123" not in str(summary),
        ),
        (
            "Shizune reçoit l'alerte sans preuves",
            any("INFRA-01" in w["title"] for w in essential["watch"])
            and "evidence" not in str(essential),
        ),
        (
            "une restauration complète rapportée ensuite vérifie INFRA-01",
            verified["state"] == "verified" and len(verified["history"]) == 2,
        ),
        (
            "chaque compte rendu n'est enregistré qu'une fois",
            len(again["history"]) == 2,
        ),
        ("plus aucune alerte urgente", urgent_after == []),
        ("le compte rendu de l'Installer n'est jamais modifié", untouched),
    ]
    details["portée"] = (
        "Module restore_report réel d'Ohana-Installer, moniteur Agent et SQLite "
        "locaux ; aucune restauration réelle"
    )
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
