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


class ConfirmedInvestigations:
    """Confirme une panne DNS avec réseau encore sain."""

    def execute(self, payload):
        operation = payload["operation"]
        now = datetime.now(UTC)

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


class TimeoutInvestigations:
    """Simule une preuve impossible à obtenir."""

    def execute(self, payload):
        now = datetime.now(UTC)

        return InvestigationResult(
            investigation_id=uuid4(),
            operation=payload["operation"],
            status="TIMEOUT",
            started_at=now,
            finished_at=now,
            duration_seconds=0,
            result={},
            error=(
                "Investigation exceeded its "
                "declared timeout"
            ),
        )


def _incident(
    sandbox,
    *,
    service: str,
    capability: str,
    message: str,
):
    return sandbox.incidents.process(
        Observation(
            node="infra-01",
            service=service,
            capability=capability,
            status=ObservationStatus.UNHEALTHY,
            success=False,
            message=message,
            source=capability,
            id=uuid4(),
            timestamp=sandbox.clock(),
            metadata={
                "device_id": "infra-01",
            },
        )
    )


def run() -> dict:
    with environment() as s:
        checks: list[tuple[str, bool]] = []

        # =================================================
        # 1. CONFIRMED
        # =================================================

        confirmed_incident = _incident(
            s,
            service="dns",
            capability="dns.health",
            message="DNS resolution failed",
        )

        s.expertise.investigations = (
            ConfirmedInvestigations()
        )

        ai_dispatches: list[dict] = []

        def dispatch(payload):
            ai_dispatches.append(payload)
            return None

        s.expertise.set_ai_dispatcher(dispatch)

        confirmed_outcome = s.expertise.diagnose(
            confirmed_incident.incident_id
        )

        confirmed_updated = s.incidents.get(
            confirmed_incident.incident_id
        )

        confirmed_assessment = incident_assessment(
            confirmed_updated
        )

        confirmed_diagnostic = [
            event
            for event in confirmed_updated.events
            if event.kind == "diagnostic"
        ][-1]

        checks.extend(
            [
                (
                    (
                        "CONFIRMED vient d'une "
                        "preuve déterministe"
                    ),
                    (
                        confirmed_diagnostic.payload.get(
                            "epistemic_status"
                        )
                        == "confirmed_by_probe"
                        and confirmed_diagnostic.payload.get(
                            "diagnostic_level"
                        )
                        == "CONFIRMED"
                    ),
                ),
                (
                    (
                        "CONFIRMED ne possède "
                        "aucun confirmation_gap"
                    ),
                    (
                        confirmed_assessment[
                            "confirmation_gap"
                        ]
                        == []
                    ),
                ),
                (
                    (
                        "CONFIRMED autorise "
                        "action_required"
                    ),
                    (
                        confirmed_outcome.decision
                        == "action_required"
                        and confirmed_assessment[
                            "diagnostic_level"
                        ]
                        == "CONFIRMED"
                    ),
                ),
                (
                    (
                        "CONFIRMED ne sollicite "
                        "pas Katsuyu AI"
                    ),
                    ai_dispatches == [],
                ),
            ]
        )

        # =================================================
        # 2. INSUFFICIENT_CONTEXT
        # =================================================

        insufficient_incident = _incident(
            s,
            service="memory",
            capability="memory.health",
            message="Memory is unhealthy",
        )

        s.expertise.investigations = (
            TimeoutInvestigations()
        )

        s.expertise.set_ai_dispatcher(
            lambda _payload: None
        )

        insufficient_outcome = s.expertise.diagnose(
            insufficient_incident.incident_id
        )

        insufficient_updated = s.incidents.get(
            insufficient_incident.incident_id
        )

        insufficient_assessment = (
            incident_assessment(
                insufficient_updated
            )
        )

        insufficient_diagnostic = [
            event
            for event in insufficient_updated.events
            if event.kind == "diagnostic"
        ][-1]

        checks.extend(
            [
                (
                    (
                        "TIMEOUT produit "
                        "INSUFFICIENT_CONTEXT"
                    ),
                    (
                        insufficient_outcome.status
                        == "INSUFFICIENT_CONTEXT"
                        and insufficient_assessment[
                            "diagnostic_level"
                        ]
                        == "INSUFFICIENT_CONTEXT"
                    ),
                ),
                (
                    (
                        "INSUFFICIENT_CONTEXT "
                        "identifie les preuves manquantes"
                    ),
                    bool(
                        insufficient_assessment[
                            "confirmation_gap"
                        ]
                    ),
                ),
                (
                    (
                        "INSUFFICIENT_CONTEXT "
                        "reste en watch"
                    ),
                    (
                        insufficient_outcome.decision
                        == "watch"
                        and insufficient_assessment[
                            "decision"
                        ]
                        == "watch"
                    ),
                ),
                (
                    (
                        "INSUFFICIENT_CONTEXT "
                        "n'est jamais confirmé"
                    ),
                    (
                        insufficient_diagnostic.payload.get(
                            "epistemic_status"
                        )
                        == "insufficient_context"
                    ),
                ),
            ]
        )

        # =================================================
        # 3. PROBABLE
        # =================================================

        probable_incident = _incident(
            s,
            service="zwave-js",
            capability="node.health",
            message=(
                "Repeated transmission failures"
            ),
        )

        s.expertise.record_ai_result(
            probable_incident.incident_id,
            uuid4(),
            {
                "analysis_version": 2,
                "verdict": "KO",
                "generated_at": (
                    "2026-09-21T12:00:00Z"
                ),
                "model_id": "sandbox",
                "model_sha256": "a" * 64,
                "interpretation": (
                    "Plusieurs éléments sont "
                    "compatibles avec une "
                    "dégradation de communication."
                ),
                "summary": (
                    "Une cause probable reste "
                    "à confirmer."
                ),
                "findings": [
                    {
                        "code": (
                            "ZWAVE.TRANSMISSION"
                        ),
                        "evidence": (
                            "Erreurs de transmission "
                            "répétées."
                        ),
                        "confidence": 1,
                    }
                ],
                "hypotheses": [
                    {
                        "statement": (
                            "La communication avec "
                            "le nœud ciblé pourrait "
                            "être dégradée."
                        ),
                        "confidence": 0.82,
                        "possible_causes": [
                            (
                                "liaison radio "
                                "instable"
                            )
                        ],
                        "supporting_evidence": [
                            (
                                "échecs de "
                                "transmission répétés"
                            )
                        ],
                        "contradicting_evidence": [
                            (
                                "aucune mesure directe "
                                "du nœud"
                            )
                        ],
                    }
                ],
                "missing_context": [
                    (
                        "Vérifier directement "
                        "l'état du nœud ciblé."
                    )
                ],
                "recommended_investigation": [
                    (
                        "Contrôler l'état réel "
                        "du nœud avant toute action."
                    )
                ],
                "metrics": {
                    "prompt_tokens": 10,
                    "completion_tokens": 10,
                    "ttft_ms": 1,
                    "tokens_per_second": 10,
                    "duration_seconds": 1,
                },
            },
        )

        probable_updated = s.incidents.get(
            probable_incident.incident_id
        )

        probable_assessment = incident_assessment(
            probable_updated
        )

        probable_diagnostic = [
            event
            for event in probable_updated.events
            if event.kind == "diagnostic"
        ][-1]

        checks.extend(
            [
                (
                    (
                        "PROBABLE reste une "
                        "hypothèse Katsuyu"
                    ),
                    (
                        probable_diagnostic.payload.get(
                            "epistemic_status"
                        )
                        == "hypothesis"
                        and probable_diagnostic.payload.get(
                            "diagnostic_level"
                        )
                        == "PROBABLE"
                    ),
                ),
                (
                    (
                        "PROBABLE expose ce qui "
                        "manque pour confirmer"
                    ),
                    (
                        probable_assessment[
                            "confirmation_gap"
                        ]
                        == [
                            (
                                "Vérifier directement "
                                "l'état du nœud ciblé."
                            )
                        ]
                    ),
                ),
                (
                    (
                        "PROBABLE demande "
                        "une investigation"
                    ),
                    (
                        probable_assessment[
                            "decision"
                        ]
                        == "investigate"
                    ),
                ),
                (
                    (
                        "PROBABLE n'autorise "
                        "jamais action_required"
                    ),
                    (
                        probable_assessment[
                            "decision"
                        ]
                        != "action_required"
                    ),
                ),
                (
                    (
                        "la projection conserve "
                        "le niveau PROBABLE"
                    ),
                    (
                        probable_assessment[
                            "diagnostic_level"
                        ]
                        == "PROBABLE"
                    ),
                ),
            ]
        )

        return {
            "passed": all(
                passed
                for _, passed in checks
            ),
            "checks": checks,
            "details": {
                "CONFIRMED": (
                    confirmed_assessment[
                        "diagnostic_level"
                    ]
                ),
                "PROBABLE": (
                    probable_assessment[
                        "diagnostic_level"
                    ]
                ),
                "INSUFFICIENT_CONTEXT": (
                    insufficient_assessment[
                        "diagnostic_level"
                    ]
                ),
                "décision CONFIRMED": (
                    confirmed_assessment[
                        "decision"
                    ]
                ),
                "décision PROBABLE": (
                    probable_assessment[
                        "decision"
                    ]
                ),
                "décision insuffisante": (
                    insufficient_assessment[
                        "decision"
                    ]
                ),
            },
        }