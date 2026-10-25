"""Phase 10: published archives are read again and compared with their record.

A directory stands in for iCloud. The real verifier streams the latest archive
of each target, the real reporter applies the weekly policy, and Tsunade's
preventive monitor turns the outcome into what Vision and Shizune show: a proven
alteration is urgent, an unreachable remote proves nothing, and nothing is ever
repaired or deleted by the check.
"""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from ohana_agent.api.service import AdministrationService
from ohana_agent.infrastructure.repository import InfrastructureConfigurationRepository
from ohana_agent.plugins.backup.archive_integrity import ArchiveIntegrityReporter
from ohana_agent.plugins.backup.archive_verifier import ArchiveVerifier
from ohana_agent.plugins.backup.config import (
    BackupConfig,
    BackupTarget,
    InfraBackupConfig,
)
from ohana_agent.tsunade.incidents import TsunadeIncidentRepository
from ohana_agent.tsunade.preventive import TsunadePreventiveMonitor
from scenarios._archives import (
    REMOTE,
    DirectoryRemote,
    age_body,
    publish_haos,
    publish_infra,
)

PARIS = ZoneInfo("Europe/Paris")


class _Sync:
    """Run the background pass in the calling thread."""

    def __init__(self, target, args, name, daemon):
        self.target, self.args = target, args

    def start(self):
        self.target(*self.args)

    def is_alive(self):
        return False


class _Clock:
    def __init__(self) -> None:
        self.mono = 0.0
        self.wall = datetime.now(UTC)

    def read(self) -> float:
        return self.mono

    def advance(self, **kwargs) -> None:
        delta = timedelta(**kwargs)
        self.mono += delta.total_seconds()
        self.wall += delta


def _config() -> BackupConfig:
    return BackupConfig(
        targets=(
            BackupTarget(id="ha-01", label="HA-01", url="http://ha", schedule="0 2 * * 6"),
        ),
        rclone_remote=REMOTE,
        infra_01=InfraBackupConfig(enabled=True),
    )


def run() -> dict:
    checks: list[tuple[str, bool]] = []
    details: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-archives-") as tmp:
        root = Path(tmp)
        remote_root = root / "remote"
        remote = DirectoryRemote(remote_root)
        body = age_body()
        publish_infra(remote_root, "20261024T020000Z", age_body(1024))
        infra_archive = publish_infra(remote_root, "20261025T030000Z", body)
        publish_haos(remote_root, "ha-01", "20261025T000000Z", b"haos tar " * 200_000)

        incidents = TsunadeIncidentRepository(root / "control.db")
        monitor = TsunadePreventiveMonitor(root / "control.db")
        service = AdministrationService(
            infrastructure_repository=InfrastructureConfigurationRepository(
                root / "infrastructure.yaml"
            ),
            incident_repository=incidents,
            preventive_monitor=monitor,
            job_repository=None,
        )
        clock = _Clock()
        reporter = ArchiveIntegrityReporter(
            ArchiveVerifier(_config(), reader=remote, clock=lambda: clock.wall),
            record=monitor.record_archive_check,
            last_check=monitor.last_archive_check,
            thread_factory=_Sync,
            monotonic_clock=clock.read,
            now=lambda: clock.wall,
        )
        service.archive_integrity = reporter
        try:
            for target in ("ha-01", "infra-01"):
                monitor.record_backup_success(target, clock.wall)
            reporter.start()
            reporter.tick()
            before_delay = monitor.last_archive_check("infra-01")
            clock.advance(hours=1)
            reporter.tick()
            intact = {t: monitor.last_archive_check(t) for t in ("ha-01", "infra-01")}
            clean = service.read_preventive_summary()
            posture = {t["target"]: t for t in service.read_restore_tests()["targets"]}

            clock.advance(days=2)
            reporter.tick()
            unchanged = monitor.last_archive_check("infra-01")["checked_at"] == (
                intact["infra-01"]["checked_at"]
            )

            # Silent alteration on the remote: one flipped byte, same size.
            altered = bytearray(infra_archive.read_bytes())
            altered[100] ^= 0xFF
            infra_archive.write_bytes(bytes(altered))
            started = service.request_archive_check({"target": "infra-01"})
            bad = monitor.last_archive_check("infra-01")
            summary = service.read_preventive_summary()
            essential = service.read_companion_summary()["preventive"]
            urgent = next(
                i for i in summary["watch"] if i["subject"] == "infra-01:integrity"
            )

            remote.online = False
            service.request_archive_check({"target": "infra-01"})
            offline = monitor.last_archive_check("infra-01")
            offline_item = next(
                i
                for i in monitor.summary()["watch"]
                if i["subject"] == "infra-01:integrity"
            )
            remote.online = True
            try:
                service.request_archive_check({"target": "nowhere"})
                refused = False
            except ValueError:
                refused = True
            infra_archive.write_bytes(body)
            service.request_archive_check({"target": "infra-01"})
            healed = monitor.last_archive_check("infra-01")
            files_after = sorted(p.name for p in remote_root.rglob("*") if p.is_file())
        finally:
            monitor.close()
            incidents.close()

    checks += [
        (
            "première passe 30 minutes après le démarrage, pas avant",
            before_delay is None,
        ),
        (
            "archives INFRA-01 et HAOS relues : taille et SHA-256 conformes",
            intact["infra-01"]["outcome"] == "ok"
            and intact["ha-01"]["outcome"] == "ok"
            and intact["infra-01"]["backup_ref"] == "20261025T030000Z",
        ),
        (
            "chiffrement age confirmé pour INFRA-01 sans rien déchiffrer",
            intact["infra-01"]["encrypted"] is True
            and posture["infra-01"]["integrity"]["encrypted"] is True,
        ),
        (
            "archives intactes : aucune alerte d'intégrité",
            all(i["subject"] not in {"infra-01:integrity", "ha-01:integrity"}
                for i in clean["watch"]),
        ),
        ("même archive non relue avant une semaine", unchanged),
        (
            "octet altéré sans changer la taille : empreinte différente détectée",
            bad["outcome"] == "hash_mismatch" and started["started"] == ["infra-01"],
        ),
        (
            "altération prouvée : urgente, citée à Shizune sans preuves",
            urgent["urgent"] is True
            and summary["conclusion"].startswith("Intervention à prévoir")
            and any("altérée" in w["title"] for w in essential["watch"])
            and "evidence" not in str(essential),
        ),
        (
            "remote illisible : rien de prouvé, alerte non urgente",
            offline["outcome"] == "unreadable" and offline_item["urgent"] is False,
        ),
        ("cible inconnue refusée", refused),
        (
            "archive rétablie : contrôle de nouveau conforme",
            healed["outcome"] == "ok",
        ),
        (
            "le contrôle ne modifie ni ne supprime aucune archive",
            len(files_after) == 6,
        ),
    ]
    details["portée"] = (
        "Agent, vérificateur, rapporteur et SQLite locaux ; un dossier remplace "
        "iCloud ; sans rclone, sans Katsuyu et sans déchiffrement"
    )
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
