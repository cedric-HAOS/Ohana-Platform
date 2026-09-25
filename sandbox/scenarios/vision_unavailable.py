"""« Ohana-Vision indisponible » through host.health, without touching systemd.

Production host health detected an inactive ohana-vision.service but only
exported it to Vision and Home Assistant: Tsunade never opened an incident, so
this controlled failure was ruled out in Phase 1. Only systemctl answers are
simulated; the host monitor, reporter, event bus, Tsunade handler, incident
store and investigation executor are the production classes.
"""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

from ohana_agent.core.events import EventBus
from ohana_agent.observation.events import HostHealthObserved
from ohana_agent.plugins.mqtt.host_health import (
    HostHealthMonitor,
    HostHealthObservationMapper,
    HostHealthReporter,
    SystemHostProbe,
)
from ohana_agent.runtime.administration_bootstrap import TsunadeObservationHandler
from ohana_agent.tsunade.expertise import TsunadeExpertiseService
from ohana_agent.tsunade.incidents import TsunadeIncidentRepository
from ohana_agent.tsunade.investigations import InvestigationExecutor


class Systemctl:
    """Answer the three systemctl calls of the host probe."""

    def __init__(self) -> None:
        self.vision_active = False

    def __call__(self, command, **_kwargs):
        arguments = command[1:]
        if arguments[:2] == ["is-active", "ohana-vision.service"]:
            return SimpleNamespace(returncode=0 if self.vision_active else 3, stdout="")
        if arguments[:1] == ["show"]:
            return SimpleNamespace(returncode=0, stdout="0\n")
        return SimpleNamespace(returncode=0, stdout="")


def _wait(predicate, timeout: float = 5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if value := predicate():
            return value
        time.sleep(0.05)
    return None


def run() -> dict:
    checks: list[tuple[str, bool]] = []
    details: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-host-") as temporary:
        root = Path(temporary)
        systemctl_file = root / "systemctl"
        systemctl_file.write_text("", encoding="utf-8")
        systemctl = Systemctl()
        monitor = HostHealthMonitor(
            SystemHostProbe(
                proc_root=root / "proc",
                sys_root=root / "sys",
                systemctl_path=systemctl_file,
                disk_usage=lambda _path: SimpleNamespace(total=100, used=10, free=90),
                runner=systemctl,
            )
        )
        incidents = TsunadeIncidentRepository(root / "incidents.db")
        started: list[str] = []
        expertise = TsunadeExpertiseService(
            incidents=incidents,
            investigations=InvestigationExecutor(
                plugins=None,  # type: ignore[arg-type] - no plugin probe here.
                host_health_reader=lambda: monitor.collect().to_dict(),
            ),
        )
        original_start = expertise.start

        def start(incident_id, **kwargs):
            started.append(str(incident_id))
            original_start(incident_id, **kwargs)

        expertise.start = start
        bus = EventBus()
        bus.subscribe(
            HostHealthObserved,
            TsunadeObservationHandler(
                incidents=incidents,
                expertise=expertise,
                administration=SimpleNamespace(),  # type: ignore[arg-type]
                logs_config=SimpleNamespace(enabled=False, sources=[]),
                notifications=None,
            ),
        )
        mapper = HostHealthObservationMapper()
        reporter = HostHealthReporter(
            monitor,
            sinks=(
                lambda snapshot: bus.publish(
                    HostHealthObserved(mapper.to_observation(snapshot))
                ),
            ),
            interval_seconds=0.01,
        )
        try:
            reporter.start()  # ohana-vision.service inactive
            incident = _wait(
                lambda: next(
                    (i for i in incidents.list() if i.capability_id == "host.health"),
                    None,
                )
            )
            decision = _wait(
                lambda: (
                    incident
                    and (incidents.get(incident.incident_id).latest_decision or None)
                )
            )
            checks += [
                (
                    "Vision arrêtée : host.health ouvre un incident Tsunade",
                    incident is not None
                    and incident.service_id == "ohana-host"
                    and "systemd_units_inactive" in incident.message,
                ),
                (
                    "Tsunade confirme par la sonde service.status, sans IA",
                    decision is not None
                    and decision.get("epistemic_status") == "confirmed_by_probe"
                    and decision.get("decision") == "action_required",
                ),
            ]
            time.sleep(0.02)
            reporter.tick()  # still inactive
            repeated = incidents.get(incident.incident_id)
            checks.append(
                (
                    "Vision toujours arrêtée : même incident, aucune nouvelle expertise",
                    repeated.occurrence_count == 2 and len(started) == 1,
                )
            )
            systemctl.vision_active = True
            time.sleep(0.02)
            reporter.tick()
            resolved = incidents.get(incident.incident_id)
            checks.append(
                (
                    "Vision redémarrée : l'incident se résout seul",
                    resolved.state == "resolved",
                )
            )
            details["incident"] = f"{incident.node_id} / host.health"
        finally:
            reporter.stop()
            incidents.close()
    details["portée"] = (
        "Moniteur, rapporteur, bus, Tsunade, incidents et investigations réels ; "
        "réponses systemctl simulées"
    )
    details["limites"] = "Aucun service réellement arrêté ; hôte Windows du lab"
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
