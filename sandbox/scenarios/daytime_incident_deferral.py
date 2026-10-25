"""Phase 6: daytime incident work waits for the 05:00 batch instead of expiring.

Bubule is off by design outside its 05:00 cycle. Until now an incident raised in
the daytime queued an AI analysis and a log check that nobody could take: both
expired after 15 minutes (33 of 34 timeouts between 11 and 24 October). They now
keep their place until the next 05:00 wake, which the real service sends once;
a backup asked by hand is not deferred, and a day with 25 hours is counted in
real hours.
"""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from ohana_agent.api.service import AdministrationService
from ohana_agent.infrastructure.repository import InfrastructureConfigurationRepository
from ohana_agent.jobs.repository import DistributedJobRepository

PARIS = ZoneInfo("Europe/Paris")
MAC = "AA:BB:CC:DD:EE:FF"
INCIDENT = "55555555-5555-4555-8555-555555555555"
AI = {
    "incident_id": INCIDENT,
    "question": "Pourquoi ?",
    "evidence": [{"source": "x", "content": "y"}],
}


class Clock:
    def __init__(self, paris: datetime) -> None:
        self.now = paris.astimezone(UTC)

    def __call__(self) -> datetime:
        return self.now


def _payload(clock: Clock, job_id: str, kind: str, parameters: dict, timeout: int = 900):
    return {
        "protocol_version": 1,
        "job_id": job_id,
        "type": kind,
        "created_at": clock.now.isoformat(),
        "parameters": parameters,
        "timeout": timeout,
    }


def _logs(clock: Clock) -> dict:
    return {
        "sources": ["ha-01"],
        "window_started_at": (clock.now - timedelta(hours=1)).isoformat(),
        "window_ended_at": clock.now.isoformat(),
        "max_bytes_per_source": 1048576,
    }


def _stack(root: Path, paris: datetime):
    clock = Clock(paris)
    infra = root / "infrastructure.yaml"
    infra.write_text("{}\n", encoding="utf-8")
    jobs = DistributedJobRepository(
        root / f"jobs-{paris:%m%d}.db", clock=clock, worker_available_seconds=30
    )
    jobs.register_worker(
        {
            "worker_id": "katsuyu-bubule",
            "capabilities": ["ai.inference", "logs.health_check", "backup.infra"],
            "platform": "Windows 11",
            "worker_version": "0.13.2",
            "wake_on_lan_mac_address": MAC,
        }
    )
    clock.now += timedelta(seconds=31)
    sent: list[str] = []
    service = AdministrationService(
        infrastructure_repository=InfrastructureConfigurationRepository(infra),
        job_repository=jobs,
        wake_timeout_seconds=180,
        wake_sender=sent.append,
        wake_enabled=True,
        wake_batch_window_seconds=600,
        wake_planned_window_start_hour=0,
        wake_planned_window_end_hour=5,
    )
    return clock, jobs, service, sent


def run() -> dict:
    checks: list[tuple[str, bool]] = []
    details: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-deferral-") as tmp:
        root = Path(tmp)
        clock, jobs, service, sent = _stack(root, datetime(2026, 8, 19, 10, 0, tzinfo=PARIS))
        try:
            ai_id = "77777777-7777-4777-8777-777777777777"
            logs_id = "88888888-8888-4888-8888-888888888888"
            backup_id = "99999999-9999-4999-8999-999999999999"
            service.create_job(_payload(clock, ai_id, "ai.inference", AI))
            service.create_job(_payload(clock, logs_id, "logs.health_check", _logs(clock)))
            service.create_job(
                _payload(
                    clock,
                    backup_id,
                    "backup.infra",
                    {
                        "backup_id": "20260819T080000Z",
                        "recipient": "age1" + "q" * 58,
                        "compression_level": 6,
                    },
                    timeout=3600,
                )
            )
            ai_timeout = jobs.get(ai_id).timeout
            logs_timeout = jobs.get(logs_id).timeout
            backup_timeout = jobs.get(backup_id).timeout

            clock.now += timedelta(minutes=16)  # the old expiry
            jobs.get(ai_id)
            after_quarter = jobs.get(ai_id).status.value, jobs.get(logs_id).status.value
            service.dispatch_due_wake_requests(now=clock.now)
            no_daytime_wake = sent == []

            clock.now += timedelta(hours=10)
            service.dispatch_due_wake_requests(now=clock.now)
            evening = jobs.get(ai_id).status.value, no_daytime_wake and sent == []

            clock.now = datetime(2026, 8, 20, 5, 0, 30, tzinfo=PARIS).astimezone(UTC)
            service.dispatch_due_wake_requests(now=clock.now)
            woken = list(sent)
            still_waiting = jobs.get(ai_id).status.value
        finally:
            jobs.close()

        clock, jobs, service, _ = _stack(root, datetime(2026, 10, 24, 10, 0, tzinfo=PARIS))
        try:
            service.create_job(_payload(clock, ai_id, "ai.inference", AI))
            change_timeout = jobs.get(ai_id).timeout
        finally:
            jobs.close()

    checks += [
        (
            "incident de journée : IA et journaux attendent le prochain 05:00",
            ai_timeout == 900 + 68369 + 180 and logs_timeout == ai_timeout,
        ),
        ("une sauvegarde demandée à la main n'est pas reportée", backup_timeout == 3600),
        (
            "après 16 minutes (ancienne échéance) les travaux attendent toujours",
            after_quarter == ("WAITING_WORKER", "WAITING_WORKER"),
        ),
        ("Bubule n'est pas réveillé en journée", no_daytime_wake and evening[1]),
        (
            "à 05:00 un seul réveil est envoyé, le travail attend toujours Bubule",
            woken == [MAC] and still_waiting == "WAITING_WORKER",
        ),
        (
            "nuit du changement d'heure : 25 heures comptées en heures réelles",
            change_timeout == 900 + 71969 + 180,
        ),
    ]
    details["portée"] = (
        "Service et file de jobs réels, horloge simulée, Wake-on-LAN enregistré ; "
        "sans Bubule ni Katsuyu"
    )
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
