"""Phase 5: a silent Agent component becomes an exploitable observation.

The Agent records the last useful activity of its scheduler, Vision delivery,
Tsunade handler and administration loop. One component going silent past its
bound must degrade host.health, open a Tsunade incident diagnosed by the
deterministic agent.vitals procedure (no AI) and resolve once it works again.
Only systemctl answers are simulated; vitals, host monitor, reporter, event
bus, Tsunade handler, incidents and investigations are the production classes.
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
from ohana_agent.runtime.vitals import AgentVitals
from ohana_agent.tsunade.expertise import TsunadeExpertiseService
from ohana_agent.tsunade.incidents import TsunadeIncidentRepository
from ohana_agent.tsunade.investigations import InvestigationExecutor

BOUND_SECONDS = 0.3


def _systemctl(command, **_kwargs):
    if command[1:2] == ["show"]:
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
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-vitals-") as temporary:
        root = Path(temporary)
        systemctl_file = root / "systemctl"
        systemctl_file.write_text("", encoding="utf-8")
        vitals = AgentVitals()
        vitals.declare("scheduler", label="Planificateur", max_silence_seconds=60)
        monitor = HostHealthMonitor(
            SystemHostProbe(
                proc_root=root / "proc",
                sys_root=root / "sys",
                systemctl_path=systemctl_file,
                disk_usage=lambda _path: SimpleNamespace(total=100, used=10, free=90),
                runner=_systemctl,
            ),
            vitals=vitals,
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
        vitals.declare(
            "tsunade", label="Tsunade (incidents)", max_silence_seconds=60
        )
        bus.subscribe(
            HostHealthObserved,
            TsunadeObservationHandler(
                incidents=incidents,
                expertise=expertise,
                administration=SimpleNamespace(),  # type: ignore[arg-type]
                logs_config=SimpleNamespace(enabled=False, sources=[]),
                notifications=None,
                on_processed=vitals.beater("tsunade"),
            ),
        )
        # The component that will go silent: the administration loop.
        vitals.declare(
            "administration",
            label="API d’administration",
            max_silence_seconds=BOUND_SECONDS,
        )
        vitals.beat("administration")
        vitals.beat("scheduler")
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
            reporter.start()
            healthy = not any(
                i.capability_id == "host.health" for i in incidents.list()
            )
            snapshot = monitor.collect()
            checks.append(
                (
                    "Composants actifs : host.health sain, activité datée à Paris",
                    healthy
                    and snapshot.state == "healthy"
                    and all(
                        c["state"] == "active"
                        and str(c["last_activity_at"]).endswith(("+02:00", "+01:00"))
                        for c in snapshot.agent_components
                    ),
                )
            )

            time.sleep(BOUND_SECONDS + 0.1)
            vitals.beat("scheduler")
            reporter.tick()
            incident = _wait(
                lambda: next(
                    (
                        i
                        for i in incidents.list()
                        if i.capability_id == "host.health"
                        and i.state == "active"
                    ),
                    None,
                )
            )
            decision = _wait(
                lambda: (
                    incident
                    and (incidents.get(incident.incident_id).latest_decision or None)
                )
            )
            stale = monitor.collect().stale_agent_components
            diagnostic = incident and next(
                (
                    event.payload
                    for event in incidents.get(incident.incident_id).events
                    if event.kind == "diagnostic"
                ),
                None,
            )
            checks += [
                (
                    "Boucle d'administration muette : incident host.health ouvert",
                    incident is not None
                    and "agent_components_stale" in incident.message
                    and stale == ("administration",),
                ),
                (
                    "Tsunade confirme par la sonde agent.vitals, sans IA",
                    decision is not None
                    and decision.get("epistemic_status") == "confirmed_by_probe"
                    and decision.get("decision_source") == "deterministic"
                    and bool(diagnostic)
                    and diagnostic.get("failed_investigations") == ["agent.vitals"],
                ),
            ]

            vitals.beat("administration")
            time.sleep(0.02)
            reporter.tick()
            resolved = incident and incidents.get(incident.incident_id)
            checks.append(
                (
                    "Composant reparti : l'incident se résout seul, une seule expertise",
                    bool(resolved)
                    and resolved.state == "resolved"
                    and len(started) == 1,
                )
            )
            if incident is not None:
                details["incident"] = f"{incident.node_id} / {incident.message}"
            if decision:
                details["décision"] = (
                    f"{decision.get('decision')} / {decision.get('decision_source')}"
                    f" / {decision.get('epistemic_status')}"
                )
        finally:
            reporter.stop()
            incidents.close()
    details["portée"] = (
        "Vitaux, moniteur, rapporteur, bus, Tsunade, incidents et investigations "
        "réels ; réponses systemctl simulées"
    )
    details["limites"] = (
        "Silence provoqué en cessant les battements, pas en bloquant une vraie "
        "boucle ; un Agent entièrement figé relève de Vision (lot 3)"
    )
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
