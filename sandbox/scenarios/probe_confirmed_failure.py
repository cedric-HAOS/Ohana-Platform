from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from ohana_agent.observation import (
    Observation,
    ObservationStatus,
)
from ohana_agent.tsunade.incident_summary import (
    incident_assessment,
)
from ohana_agent.tsunade.investigations import (
    InvestigationResult,
)

from scenarios._support import environment


class ConfirmedDnsInvestigations:
    """Sondes déterministes simulées, sans accès à Konoha."""

    def __init__(self) -> None:
        self.operations: list[str] = []

    def execute(self, payload):
        operation = payload["operation"]
        self.operations.append(operation)

        now = self._now

        if operation == "dns.query":
            result = {
                "success": False,
                "status": "failed",
            }
        elif operation == "network.ping":
            result = {
                "success": True,
                "status": "healthy",
            }
        else:
            raise AssertionError(
                f"Opération inattendue : {operation}"
            )

        return InvestigationResult(
            investigation_id=uuid4(),
            operation=operation,
            status="OK",
            started_at=now,
            finished_at=now,
            duration_seconds=0,
            result=result,
        )

    @property
    def _now(self):
        from datetime import UTC, datetime

        return datetime.now(UTC)


def run() -> dict:
    with environment() as s:
        # -------------------------------------------------
        # 1. Shikamaru signale une anomalie DNS.
        # -------------------------------------------------

        incident = s.incidents.process(
            Observation(
                node="infra-01",
                service="dns",
                capability="dns.resolve",
                status=ObservationStatus.UNHEALTHY,
                success=False,
                message="DNS resolution failed",
                source="dns.resolve",
                id=uuid4(),
                timestamp=s.clock(),
                metadata={
                    "device_id": "infra-01",
                },
            )
        )

        investigations = ConfirmedDnsInvestigations()

        s.expertise.investigations = investigations

        # Si ce dispatcher est appelé, le scénario doit
        # pouvoir le détecter : cette panne est suffisamment
        # déterministe pour ne nécessiter aucune IA.
        dispatched: list[dict] = []

        def dispatch(payload):
            dispatched.append(payload)
            return None

        s.expertise.set_ai_dispatcher(dispatch)

        # -------------------------------------------------
        # 2. Diagnostic Tsunade.
        # -------------------------------------------------

        outcome = s.expertise.diagnose(
            incident.incident_id
        )

        updated = s.incidents.get(
            incident.incident_id
        )

        assessment = incident_assessment(
            updated
        )

        investigation_events = [
            event
            for event in updated.events
            if event.kind == "investigation"
        ]

        diagnostic_events = [
            event
            for event in updated.events
            if event.kind == "diagnostic"
        ]

        confirmed_events = [
            event
            for event in diagnostic_events
            if event.payload.get(
                "epistemic_status"
            )
            == "confirmed_by_probe"
        ]

        confirmed = (
            confirmed_events[-1]
            if confirmed_events
            else None
        )

        measurements = {
            event.payload["operation"]:
                event.payload.get("result", {})
            for event in investigation_events
        }

        before_recovery_checks = [
            (
                (
                    "la procédure DNS exécute "
                    "les deux contrôles attendus"
                ),
                investigations.operations
                == [
                    "dns.query",
                    "network.ping",
                ],
            ),
            (
                (
                    "les deux sondes ont été "
                    "exécutées correctement"
                ),
                all(
                    event.payload.get("status")
                    == "OK"
                    for event in investigation_events
                ),
            ),
            (
                "dns.query mesure bien un échec",
                (
                    measurements.get(
                        "dns.query", {}
                    ).get("success")
                    is False
                ),
            ),
            (
                "network.ping reste sain",
                (
                    measurements.get(
                        "network.ping", {}
                    ).get("success")
                    is True
                ),
            ),
            (
                (
                    "Tsunade produit un "
                    "diagnostic déterministe"
                ),
                outcome.status == "DETERMINISTIC",
            ),
            (
                "la décision est action_required",
                outcome.decision
                == "action_required",
            ),
            (
                (
                    "la décision appartient "
                    "au moteur déterministe"
                ),
                outcome.decision_source
                == "deterministic",
            ),
            (
                "la confiance déterministe vaut 1",
                outcome.confidence == 1.0,
            ),
            (
                (
                    "la panne est explicitement "
                    "confirmée par une sonde"
                ),
                len(confirmed_events) == 1,
            ),
            (
                (
                    "seul dns.query est identifié "
                    "comme contrôle défaillant"
                ),
                (
                    confirmed is not None
                    and confirmed.payload.get(
                        "failed_investigations"
                    )
                    == ["dns.query"]
                ),
            ),
            (
                (
                    "la projection utilisateur "
                    "demande une intervention"
                ),
                (
                    assessment["state"]
                    == "action_required"
                    and assessment["decision"]
                    == "action_required"
                ),
            ),
            (
                (
                    "aucune expertise IA "
                    "n'est demandée"
                ),
                dispatched == [],
            ),
        ]

        # -------------------------------------------------
        # 3. Retour à l'état sain.
        #
        # Une nouvelle observation saine doit clôturer
        # le même incident, sans intervention artificielle
        # du Sandbox sur son état.
        # -------------------------------------------------

        healthy_at = s.clock.advance(
            minutes=5
        )

        recovered = s.incidents.process(
            Observation(
                node="infra-01",
                service="dns",
                capability="dns.resolve",
                status=ObservationStatus.HEALTHY,
                success=True,
                message="DNS healthy again",
                source="dns.resolve",
                id=uuid4(),
                timestamp=healthy_at,
                metadata={
                    "device_id": "infra-01",
                },
            )
        )

        recovered_assessment = (
            incident_assessment(recovered)
        )

        recovery_checks = [
            (
                (
                    "le retour sain concerne "
                    "le même incident"
                ),
                recovered.incident_id
                == incident.incident_id,
            ),
            (
                "l'incident est résolu",
                recovered.state == "resolved",
            ),
            (
                (
                    "la projection utilisateur "
                    "devient Résolu"
                ),
                (
                    recovered_assessment["state"]
                    == "resolved"
                    and recovered_assessment[
                        "label"
                    ]
                    == "Résolu"
                ),
            ),
            (
                (
                    "aucune IA n'est apparue "
                    "pendant le cycle"
                ),
                dispatched == [],
            ),
        ]

        checks = (
            before_recovery_checks
            + recovery_checks
        )

        return {
            "passed": all(
                passed
                for _, passed in checks
            ),
            "checks": checks,
            "details": {
                "sondes": ", ".join(
                    investigations.operations
                ),
                "dns.query": (
                    measurements[
                        "dns.query"
                    ]["success"]
                ),
                "network.ping": (
                    measurements[
                        "network.ping"
                    ]["success"]
                ),
                "expertise": outcome.status,
                "décision": outcome.decision,
                "confiance": outcome.confidence,
                "confirmation": (
                    confirmed.payload.get(
                        "epistemic_status"
                    )
                    if confirmed
                    else "absente"
                ),
                "IA demandée": len(dispatched),
                "état final": recovered.state,
            },
        }