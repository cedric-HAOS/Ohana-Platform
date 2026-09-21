from __future__ import annotations

from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from ohana_agent.observation import Observation, ObservationStatus
from ohana_agent.tsunade.incident_summary import incident_assessment

from scenarios._support import authorize, environment, job_counts, propose
from scenarios.probe_confirmed_failure import ConfirmedDnsInvestigations


def run() -> dict:
    with environment() as s:
        propose(s)
        request = authorize(s)
        target = s.jobs.latest_for_incident(
            "logs.investigate", str(s.incident.incident_id)
        )
        assert target is not None, "Collecte complémentaire absente"
        s.clock.advance(seconds=31)
        waiting = s.jobs.get(str(target.job_id))
        worker = s.jobs.worker_availability("sandbox-worker")
        counts = job_counts(s)

        class LocalProbes(ConfirmedDnsInvestigations):
            @property
            def _now(self):
                return datetime.now(ZoneInfo("Europe/Paris"))

        probes = LocalProbes()
        s.expertise.investigations = probes

        def observe(healthy: bool):
            return s.incidents.process(
                Observation(
                    node="infra-01",
                    service="dns",
                    capability="dns.resolve",
                    status=ObservationStatus.HEALTHY
                    if healthy
                    else ObservationStatus.UNHEALTHY,
                    success=healthy,
                    message="DNS healthy again" if healthy else "DNS resolution failed",
                    source="dns.resolve",
                    id=uuid4(),
                    # L'horloge accélérée est propre aux échéances de la file.
                    # Les décisions utilisent encore l'heure système.
                    timestamp=datetime.now(ZoneInfo("Europe/Paris")),
                    metadata={"device_id": "infra-01"},
                )
            )

        incident = observe(False)
        outcome = s.expertise.diagnose(incident.incident_id)
        diagnosed = s.incidents.get(incident.incident_id)
        assessment = incident_assessment(diagnosed)
        s.clock.advance(seconds=1)
        recovered = observe(True)
        checks = [
            (
                "Katsuyu indisponible avant le diagnostic",
                worker.availability.value == "UNAVAILABLE",
            ),
            ("collecte distante en attente", waiting.status.value == "WAITING_WORKER"),
            (
                "les deux contrôles locaux sont exécutés",
                probes.operations == ["dns.query", "network.ping"],
            ),
            (
                "diagnostic déterministe avec intervention requise",
                outcome.status == "DETERMINISTIC"
                and outcome.decision == "action_required",
            ),
            (
                "confirmation reliée à la mesure DNS",
                any(
                    event.kind == "diagnostic"
                    and event.payload.get("epistemic_status") == "confirmed_by_probe"
                    and event.payload.get("failed_investigations") == ["dns.query"]
                    for event in diagnosed.events
                ),
            ),
            (
                "décision exposée à l'utilisateur",
                assessment["state"] == "action_required",
            ),
            (
                "retour sain sur le même incident",
                recovered.incident_id == incident.incident_id
                and recovered.state == "resolved",
            ),
            (
                "incident initial conservé actif",
                s.incidents.get(s.incident.incident_id).state == "active",
            ),
            (
                "suivi distant toujours en attente",
                s.incidents.get_followup(str(request.request_id))["status"] == "queued"
                and s.jobs.get(str(target.job_id)).status.value == "WAITING_WORKER",
            ),
            ("aucun travail distant supplémentaire", job_counts(s) == counts),
            (
                "aucun retour du worker nécessaire",
                s.jobs.worker_availability("sandbox-worker").availability.value
                == "UNAVAILABLE",
            ),
        ]
        return {
            "passed": all(passed for _, passed in checks),
            "checks": checks,
            "details": {
                "worker": worker.availability.value,
                "diagnostic local": outcome.decision,
                "incident DNS": recovered.state,
            },
        }
