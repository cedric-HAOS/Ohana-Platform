from __future__ import annotations

from uuid import uuid4

from ohana_agent.observation import Observation, ObservationStatus
from ohana_agent.tsunade.incident_summary import incident_assessment

from scenarios._support import NoProbes, environment, restart


class StoppedTeleinformationSupervisor(NoProbes):
    """Seule l'inspection Supervisor est simulée ; aucune sonde réseau réelle."""

    def __init__(self) -> None:
        self.snapshot_nodes: list[str] = []

    def read_only_snapshot(self, node_id: str) -> dict:
        self.snapshot_nodes.append(node_id)
        if node_id != "linky-01":
            raise AssertionError(f"Cible Supervisor inattendue : {node_id}")
        return {
            "configuration_inspection": {
                "remote": {
                    "origin": "linky-01 / Supervisor",
                    "addons": [
                        {
                            "addon": "6fc079ce_teleinfo2mqtt_ohana",
                            "state": "stopped",
                        }
                    ],
                }
            }
        }


def _observation(s, *, age: int, maximum_age: int = 30) -> Observation:
    healthy = age <= maximum_age
    return Observation(
        node="linky-01",
        service="tic-linky",
        capability="teleinformation.freshness",
        status=ObservationStatus.HEALTHY if healthy else ObservationStatus.UNHEALTHY,
        success=healthy,
        message=(
            "Nouvelles trames Téléinformation reçues."
            if healthy
            else f"Aucune trame téléinformation reçue depuis {age} secondes."
        ),
        source="teleinformation.freshness",
        id=uuid4(),
        timestamp=s.clock(),
        metadata={
            "device_id": "linky-01",
            "mode": "direct_http",
            "source_id": "rpi-linky",
            "meter_id": "sandbox-meter",
            "maximum_age_seconds": maximum_age,
            "age_seconds": age,
        },
    )


def _diagnostics(incident) -> list[dict]:
    return [
        event.model_dump(mode="json")
        for event in incident.events
        if event.kind == "diagnostic"
    ]


def run() -> dict:
    checks = []
    with environment() as s:
        investigations = StoppedTeleinformationSupervisor()
        dispatched = []

        def dispatch(payload):
            dispatched.append(payload)
            return s.jobs.create(payload)

        s.expertise.investigations = investigations
        s.expertise.set_ai_dispatcher(dispatch)
        incident = s.incidents.process(_observation(s, age=96))
        assert incident is not None, "Incident Téléinformation absent"
        incident_id = incident.incident_id
        outcome = s.expertise.diagnose(incident_id)
        diagnosed = s.incidents.get(incident_id)
        decision = diagnosed.latest_decision or {}
        assessment = incident_assessment(diagnosed)
        original_diagnostics = _diagnostics(diagnosed)
        supervisor_events = [
            event
            for event in diagnosed.events
            if event.payload.get("source") == "supervisor.teleinformation"
        ]
        checks.extend(
            [
                (
                    "preuve Supervisor conservée dans le dossier avant le diagnostic",
                    len(supervisor_events) == 1
                    and supervisor_events[0].payload["node"] == "linky-01"
                    and supervisor_events[0].payload["configuration_inspection"][
                        "remote"
                    ]["addons"][0]["state"]
                    == "stopped"
                    and supervisor_events[0].event_id
                    < original_diagnostics[0]["event_id"],
                ),
                ("incident Téléinformation actif", diagnosed.state == "active"),
                (
                    "Supervisor consulté sur LINKY-01 avant toute IA",
                    investigations.snapshot_nodes == ["linky-01"] and not dispatched,
                ),
                (
                    "diagnostic déterministe sans job IA",
                    outcome.status == "DETERMINISTIC" and outcome.ai_job_id is None,
                ),
                (
                    "cause confirmée par Supervisor, sans preuve manquante",
                    decision.get("epistemic_status") == "confirmed_by_supervisor"
                    and decision.get("diagnostic_level") == "CONFIRMED"
                    and decision.get("confirmation_gap") == []
                    and decision.get("confidence") == 1.0,
                ),
                (
                    "preuve stopped et add-on identifiables dans la décision",
                    "stopped" in decision.get("reason", "").lower()
                    and "teleinfo2mqtt" in decision.get("conclusion", "").lower(),
                ),
                (
                    "décision investigate déterministe, sans réparation automatique",
                    outcome.decision == "investigate"
                    and outcome.decision_source == "deterministic",
                ),
                (
                    "projection CONFIRMED courante avec empreinte diagnostique",
                    assessment["decision_current"] is True
                    and assessment["diagnostic_level"] == "CONFIRMED"
                    and bool(decision.get("basis_fingerprint"))
                    and len(original_diagnostics) == 1,
                ),
            ]
        )

        # Les observations évoluent dans le temps, sans nouvelle cause.
        for occurrence, age in enumerate((156, 216, 276), start=2):
            s.clock.advance(minutes=1)
            repeated = s.incidents.process(_observation(s, age=age))
            assert repeated is not None
            s.service.list_incidents()
            current = s.incidents.get(incident_id)
            projection = incident_assessment(current)
            checks.extend(
                [
                    (
                        f"observation {occurrence} : même incident actualisé",
                        repeated.incident_id == incident_id
                        and current.occurrence_count == occurrence
                        and current.last_observed_at == s.clock()
                        and current.context.get("age_seconds") == age,
                    ),
                    (
                        f"observation {occurrence} : diagnostic confirmé toujours courant",
                        projection["decision_current"] is True
                        and projection["diagnostic_level"] == "CONFIRMED"
                        and projection["state"] == "investigate"
                        and current.latest_decision == decision,
                    ),
                    (
                        f"observation {occurrence} : aucun nouveau diagnostic ni IA",
                        _diagnostics(current) == original_diagnostics
                        and not dispatched
                        and s.jobs.count("ai.inference") == 0,
                    ),
                ]
            )

        # Relecture des bases : la stabilité ne dépend pas d'un cache mémoire.
        before_restart = s.incidents.get(incident_id).model_dump(mode="json")
        restart(s)
        s.expertise.investigations = investigations
        s.expertise.set_ai_dispatcher(dispatch)
        s.service.list_incidents()
        restored = s.incidents.get(incident_id)
        checks.extend(
            [
                (
                    "reprise SQLite : dossier et historique intégralement conservés",
                    restored.model_dump(mode="json") == before_restart,
                ),
                (
                    "reprise SQLite : diagnostic toujours courant sans nouvelle inspection",
                    incident_assessment(restored)["decision_current"] is True
                    and investigations.snapshot_nodes == ["linky-01"],
                ),
            ]
        )

        # Contrôle négatif : un changement matériel doit invalider l'empreinte.
        s.clock.advance(minutes=1)
        changed = s.incidents.process(_observation(s, age=336, maximum_age=60))
        assert changed is not None
        changed_projection = incident_assessment(s.incidents.get(incident_id))
        checks.append(
            (
                "nouveau seuil : même incident mais analyse à actualiser",
                changed.incident_id == incident_id
                and changed_projection["decision_current"] is False
                and changed_projection["state"] == "stale",
            )
        )
        s.expertise.diagnose(incident_id)
        refreshed = s.incidents.get(incident_id)
        refreshed_decision = refreshed.latest_decision or {}
        checks.append(
            (
                "réévaluation explicite : nouvelle base confirmée sans IA",
                incident_assessment(refreshed)["decision_current"] is True
                and refreshed_decision.get("diagnostic_level") == "CONFIRMED"
                and refreshed_decision.get("basis_fingerprint")
                != decision.get("basis_fingerprint")
                and investigations.snapshot_nodes == ["linky-01", "linky-01"]
                and len(_diagnostics(refreshed)) == 2,
            )
        )

        # Le retour de trames est simulé, sans démarrer de véritable add-on.
        s.clock.advance(minutes=1)
        recovered = s.incidents.process(_observation(s, age=2, maximum_age=60))
        assert recovered is not None
        recovered_projection = incident_assessment(recovered)
        checks.extend(
            [
                (
                    "nouvelles trames : résolution automatique du même incident",
                    recovered.incident_id == incident_id
                    and recovered.state == "resolved",
                ),
                (
                    "projection finale Résolu",
                    recovered_projection["state"] == "resolved"
                    and recovered_projection["label"] == "Résolu",
                ),
                (
                    "aucun incident Téléinformation actif résiduel",
                    not any(
                        item.capability_id == "teleinformation.freshness"
                        for item in s.incidents.list()
                    ),
                ),
                (
                    "diagnostics conservés après résolution",
                    _diagnostics(recovered) == _diagnostics(refreshed),
                ),
            ]
        )
        restart(s)
        s.service.list_incidents()
        final = s.incidents.get(incident_id)
        checks.extend(
            [
                (
                    "seconde reprise : résolution et historique conservés",
                    final.model_dump(mode="json") == recovered.model_dump(mode="json"),
                ),
                (
                    "aucun appel IA ni job IA ou collecte sur tout le cycle",
                    not dispatched
                    and s.jobs.count("ai.inference") == 0
                    and s.jobs.count("logs.investigate") == 0,
                ),
            ]
        )
        return {
            "passed": all(passed for _, passed in checks),
            "checks": checks,
            "details": {
                "mode": "direct_http ; observations et Supervisor simulés",
                "inspections Supervisor": len(investigations.snapshot_nodes),
                "diagnostics": len(_diagnostics(final)),
                "IA demandée": len(dispatched),
                "état final": final.state,
            },
        }
