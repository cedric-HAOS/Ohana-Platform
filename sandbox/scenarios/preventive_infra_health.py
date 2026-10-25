"""Phase 4/10: what quietly puts INFRA-01 and its backups at risk.

Three signs reach Tsunade's preventive monitor through the paths the Agent
really uses: the AdGuard replication check (a protection paused for hours),
the SD card counters of the host (writes getting slow, root turned read-only)
and the hourly iCloud session reading (expired session). The Agent service then
answers Vision (detail) and Shizune (essential). Nothing is repaired.
"""

from __future__ import annotations

import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from ohana_agent.api.service import AdministrationService
from ohana_agent.infrastructure.repository import InfrastructureConfigurationRepository
from ohana_agent.observation import ObservationStatus
from ohana_agent.observation.observation import Observation
from ohana_agent.plugins.backup.icloud_connectivity import ICloudConnectivityStatus
from ohana_agent.tsunade.incidents import TsunadeIncidentRepository
from ohana_agent.tsunade.preventive import TsunadePreventiveMonitor
from ohana_agent.tsunade.storage_health import StorageSampler

PARIS = ZoneInfo("Europe/Paris")


def _adguard(at: datetime, *, enabled: bool, until: str | None = None):
    return SimpleNamespace(
        observation=Observation(
            node="infra-01",
            service="adguard-sync",
            capability="adguard_sync.status",
            status=ObservationStatus.HEALTHY,
            success=True,
            message="Sync",
            source="adguard_sync",
            timestamp=at,
            metadata={"protection": {"enabled": enabled, "disabled_until": until}},
        )
    )


def _host(at: datetime) -> Observation:
    return Observation(
        node="infra-01",
        service="ohana-host",
        capability="host.health",
        status=ObservationStatus.HEALTHY,
        success=True,
        message="Host healthy",
        source="host-health",
        timestamp=at,
        metadata={"host_health": {"disk_percent": 12.0}},
    )


def _icloud(state: str, at: datetime) -> ICloudConnectivityStatus:
    return ICloudConnectivityStatus(
        state=state,
        connected=state == "connected",
        remote="icloud:",
        checked_at=at.isoformat(timespec="seconds"),
        last_success_at=None,
        detail=None if state == "connected" else "Invalid global session",
    )


def _stat(ios: int, sectors: int, ticks: int) -> str:
    fields = [769708, 41619, 11571482, 917647, ios, 0, sectors, ticks]
    return " ".join(str(v) for v in fields + [0] * 9)


def _titles(summary: dict) -> list[str]:
    return [item["title"] for item in summary["watch"]]


def run() -> dict:
    checks: list[tuple[str, bool]] = []
    details: dict[str, str] = {}
    now = datetime.now(PARIS).replace(microsecond=0)
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-infra-health-") as tmp:
        root = Path(tmp)
        block = root / "block" / "mmcblk0"
        block.mkdir(parents=True)
        mounts = root / "mounts"
        mounts.write_text("/dev/mmcblk0p2 / ext4 rw,noatime 0 0\n")
        (block / "stat").write_text(_stat(0, 0, 0))

        incidents = TsunadeIncidentRepository(root / "control.db")
        monitor = TsunadePreventiveMonitor(
            root / "control.db",
            storage_sampler=StorageSampler(sys_block=root / "block", mounts=mounts),
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
            calm = service.read_preventive_summary()

            # AdGuard paused for 40 minutes, then for more than three hours.
            start = now - timedelta(hours=4)
            for minute in range(0, 41, 5):
                monitor.handle_observation(
                    _adguard(start + timedelta(minutes=minute), enabled=False)
                )
            short_pause = monitor.summary(now=start + timedelta(minutes=40))
            for minute in range(45, 241, 5):
                monitor.handle_observation(
                    _adguard(
                        start + timedelta(minutes=minute),
                        enabled=False,
                        until=(now + timedelta(hours=20)).isoformat(),
                    )
                )
            long_pause = service.read_preventive_summary()
            monitor.handle_observation(_adguard(now, enabled=True))
            resumed = service.read_preventive_summary()

            # The SD card: a first reading, then 100 writes taking 400 ms each.
            monitor.record_host_health(_host(now - timedelta(minutes=2)))
            (block / "stat").write_text(_stat(100, 8192, 40_000))
            monitor.record_host_health(_host(now))
            for offset in range(1, 7):
                day = now - timedelta(days=offset)
                for minute in (0, 30):
                    monitor.record_metric(
                        "infra-01",
                        "sd_write_latency_ms",
                        120.0 if offset <= 3 else 15.0,
                        day + timedelta(minutes=minute),
                    )
            slow_card = service.read_preventive_summary()
            mounts.write_text("/dev/mmcblk0p2 / ext4 ro,relatime 0 0\n")
            monitor.record_host_health(_host(now + timedelta(minutes=1)))
            read_only = service.read_preventive_summary()

            # The iCloud session the backups depend on.
            monitor.record_icloud_status(_icloud("connected", now - timedelta(hours=2)))
            session_ok = service.read_preventive_summary()
            monitor.record_icloud_status(_icloud("session_expired", now))
            expired = service.read_preventive_summary()
            essential = service.read_companion_summary()["preventive"]
            document = service.read_restore_tests()
        finally:
            monitor.close()
            incidents.close()

    expired_item = next(
        i for i in expired["watch"] if i["rule"] == "icloud_session"
    )
    checks += [
        ("situation calme : rien à surveiller", calm["watch"] == []),
        (
            "pause AdGuard de 40 minutes : normale, rien signalé",
            all("AdGuard" not in t for t in _titles(short_pause)),
        ),
        (
            "pause AdGuard de plus de 3 heures : signalée avec sa fin",
            any("AdGuard : protection suspendue depuis 4 h" in t for t in _titles(long_pause))
            and all(not i["urgent"] for i in long_pause["watch"]),
        ),
        (
            "protection rétablie : l'alerte disparaît",
            all("AdGuard" not in t for t in _titles(resumed)),
        ),
        (
            "carte SD : écritures lentes sur trois jours signalées",
            any("carte SD lente" in t for t in _titles(slow_card)),
        ),
        (
            "racine en lecture seule : urgent",
            any(
                i["subject"] == "infra-01:readonly" and i["urgent"]
                for i in read_only["watch"]
            ),
        ),
        (
            "iCloud session ouverte : aucune alerte",
            all(i["rule"] != "icloud_session" for i in session_ok["watch"]),
        ),
        (
            "iCloud session expirée : urgent, reconnexion indiquée",
            expired_item["urgent"] is True
            and "Reconnecter iCloud" in expired_item["detail"],
        ),
        (
            "Shizune reçoit l'essentiel sans preuves",
            any("session expirée" in w["title"] for w in essential["watch"])
            and "evidence" not in str(essential),
        ),
        (
            "Vision lit l'état iCloud avec les restaurations",
            document["icloud"]["state"] == "session_expired",
        ),
        (
            "aucune réparation automatique",
            expired["automatic_actions"] is False,
        ),
    ]
    details["portée"] = (
        "Agent, moniteur préventif et SQLite locaux ; compteurs /sys simulés par "
        "des fichiers ; sans AdGuard, sans carte SD réelle, sans rclone"
    )
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
