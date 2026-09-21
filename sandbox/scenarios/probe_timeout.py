from __future__ import annotations

from datetime import UTC, datetime
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


class TimeoutInvestigations:
    """Simule une sonde indisponible sans toucher au système réel."""

    def __init__(self) -> None:
        self.operations: list[str] = []

    def execute(self, payload):
        self.operations.append(payload["operation"])

        now = datetime.now(UTC)

        return InvestigationResult(
            investigation_id=uuid4(),
            operation=payload["operation"],
            status="TIMEOUT",
            started_at=now,
            finished_at=now,
            duration_seconds=0,
            result={},
            error="Investigation exceeded its declared timeout",
        )


def run() -> dict:
    with environment() as s:
        # -------------------------------------------------
        # 1. Création d'un véritable incident mémoire.
        #
        # Il correspond à une procédure déterministe connue
        # de Tsunade : memory.status.
        # -------------------------------------------------

        incident = s.incidents.process(
            Observation(
                node="infra-01",
                service="memory",
                capability="memory.health",
                status=ObservationStatus.UNHEALTHY,
                success=False,
                message="Memory is unhealthy",
                source="memory.health",
                id=uuid4(),
                timestamp=s.clock(),
                metadata={
                    "device_id": "infra-01",
                },
            )
        )

        investigations = TimeoutInvestigations()

        # Aucune vraie sonde n'est appelée.
        s.expertise.investigations = investigations

        # Katsuyu AI est volontairement indisponible.
        #
        # Cela permet de vérifier que Tsunade ne transforme
        # pas le TIMEOUT en certitude lorsqu'elle ne peut pas
        # demander une seconde opinion.
        s.expertise.set_ai_dispatcher(
            lambda _payload: None
        )

        ai_before = s.jobs.count("ai.inference")

        # -------------------------------------------------
        # 2. Cycle de diagnostic réel Tsunade.
        # -------------------------------------------------

        outcome = s.expertise.diagnose(
            incident.incident_id
        )

        updated = s.incidents.get(
            incident.incident_id
        )

        assessment = incident_assessment(updated)

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

        timeout_event = (
            investigation_events[-1]
            if investigation_events
            else None
        )

        diagnostic = (
            diagnostic_events[-1]
            if diagnostic_events
            else None
        )

        ai_after = s.jobs.count("ai.inference")

        # -------------------------------------------------
        # 3. Vérification de la persistance.
        #
        # On contrôle la projection réellement stockée,
        # pas seulement l'objet retourné par diagnose().
        # -------------------------------------------------

        checks = [
            (
                "la procédure memory.status est exécutée",
                investigations.operations
                == ["memory.status"],
            ),
            (
                "le timeout reste une limitation de sonde",
                (
                    timeout_event is not None
                    and timeout_event.payload.get(
                        "status"
                    )
                    == "TIMEOUT"
                ),
            ),
            (
                (
                    "le timeout ne confirme jamais "
                    "une panne mémoire"
                ),
                len(confirmed_events) == 0,
            ),
            (
                (
                    "Tsunade déclare le contexte "
                    "insuffisant"
                ),
                outcome.status
                == "INSUFFICIENT_CONTEXT",
            ),
            (
                "la décision Tsunade reste watch",
                (
                    outcome.decision == "watch"
                    and outcome.decision_source
                    == "fallback"
                ),
            ),
            (
                (
                    "l'incident reste actif "
                    "sans faux diagnostic"
                ),
                updated.state == "active",
            ),
            (
                (
                    "l'état d'expertise devient "
                    "insufficient_context"
                ),
                updated.expertise_state
                == "insufficient_context",
            ),
            (
                (
                    "la projection incident "
                    "conserve la décision watch"
                ),
                assessment["decision"] == "watch",
            ),
            (
                (
                    "une justification exploitable "
                    "est conservée"
                ),
                bool(assessment["reason"]),
            ),
            (
                (
                    "une action suivante "
                    "est proposée"
                ),
                bool(
                    assessment[
                        "recommended_action"
                    ]
                ),
            ),
            (
                (
                    "le diagnostic est marqué "
                    "insufficient_context"
                ),
                (
                    diagnostic is not None
                    and diagnostic.payload.get(
                        "epistemic_status"
                    )
                    == "insufficient_context"
                ),
            ),
            (
                (
                    "le TIMEOUT reste visible "
                    "dans les faits"
                ),
                any(
                    fact
                    == "memory.status: TIMEOUT"
                    for fact in outcome.facts
                ),
            ),
            (
                (
                    "aucun job IA n'est créé "
                    "quand Katsuyu est indisponible"
                ),
                ai_after == ai_before,
            ),
        ]

        return {
            "passed": all(
                passed
                for _, passed in checks
            ),
            "checks": checks,
            "details": {
                "sonde": "memory.status",
                "résultat sonde": (
                    timeout_event.payload.get(
                        "status"
                    )
                    if timeout_event
                    else "absent"
                ),
                "expertise": outcome.status,
                "décision": outcome.decision,
                "source décision": (
                    outcome.decision_source
                ),
                "incident": updated.state,
                "état expertise": (
                    updated.expertise_state
                ),
                "confirmations sonde": len(
                    confirmed_events
                ),
                "jobs IA créés": (
                    ai_after - ai_before
                ),
            },
        }