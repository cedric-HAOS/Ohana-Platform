from __future__ import annotations

import json

from ohana_agent.observation import (
    Observation,
    ObservationStatus,
)
from ohana_agent.tsunade.incident_summary import (
    incident_assessment,
)
from ohana_agent.tsunade.investigations import (
    InvestigationExecutor,
)

from scenarios._support import environment


SECRET = (
    "https://admin:SuperSecretPassword@"
    "infra-01.ohana.lan/private?token=ABC123"
)


class ExplodingPlugins:
    """Fausse couche plugin ne touchant jamais l'infrastructure réelle."""

    def test(self, plugin_id):
        raise RuntimeError(
            f"Connexion impossible vers {SECRET}"
        )

    def read(self, plugin_id):
        raise RuntimeError(
            f"Lecture impossible vers {SECRET}"
        )


def _contains_secret(value) -> bool:
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        default=str,
    )

    return (
        SECRET in serialized
        or "SuperSecretPassword" in serialized
        or "ABC123" in serialized
    )


def run() -> dict:
    with environment() as s:
        # -------------------------------------------------
        # 1. Incident DNS réel du point de vue Tsunade.
        #
        # La procédure connue déclenche dns.query puis,
        # faute de confirmation, network.ping.
        # -------------------------------------------------

        incident = s.incidents.process(
            Observation(
                node="infra-01",
                service="dns",
                capability="dns.health",
                status=ObservationStatus.UNHEALTHY,
                success=False,
                message="DNS is unhealthy",
                source="dns.health",
                timestamp=s.clock(),
                metadata={
                    "device_id": "infra-01",
                },
            )
        )

        # -------------------------------------------------
        # 2. Véritable InvestigationExecutor.
        #
        # Ce n'est pas un InvestigationResult fabriqué :
        # on fait réellement lever une exception dans
        # l'exécuteur afin de tester son assainissement.
        # -------------------------------------------------

        executor = InvestigationExecutor(
            plugins=ExplodingPlugins(),
            host_health_reader=lambda: {},
            jobs=s.jobs,
        )

        s.expertise.investigations = executor

        # Katsuyu volontairement indisponible :
        # la sonde KO ne doit donc jamais être transformée
        # en certitude faute d'une autre source.
        s.expertise.set_ai_dispatcher(
            lambda _payload: None
        )

        ai_before = s.jobs.count(
            "ai.inference"
        )

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

        confirmed = [
            event
            for event in diagnostic_events
            if event.payload.get(
                "epistemic_status"
            )
            == "confirmed_by_probe"
        ]

        ai_after = s.jobs.count(
            "ai.inference"
        )

        # Les deux opérations DNS doivent échouer
        # proprement sous forme de KO.
        statuses = [
            event.payload.get("status")
            for event in investigation_events
        ]

        errors = [
            event.payload.get("error")
            for event in investigation_events
        ]

        # On inspecte également l'intégralité de
        # l'incident persistant pour détecter toute fuite.
        incident_has_secret = _contains_secret(
            updated.model_dump(mode="json")
        )

        checks = [
            (
                (
                    "les sondes produisent "
                    "des résultats KO"
                ),
                (
                    len(investigation_events) == 2
                    and statuses == ["KO", "KO"]
                ),
            ),
            (
                (
                    "seul le type d'exception "
                    "est conservé"
                ),
                errors == [
                    "RuntimeError",
                    "RuntimeError",
                ],
            ),
            (
                (
                    "le message sensible "
                    "de l'exception est supprimé"
                ),
                not incident_has_secret,
            ),
            (
                (
                    "un KO de sonde ne confirme "
                    "jamais la panne DNS"
                ),
                len(confirmed) == 0,
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
                "la décision reste watch",
                (
                    outcome.decision == "watch"
                    and outcome.decision_source
                    == "fallback"
                ),
            ),
            (
                "l'incident reste actif",
                updated.state == "active",
            ),
            (
                (
                    "l'expertise reste "
                    "insufficient_context"
                ),
                updated.expertise_state
                == "insufficient_context",
            ),
            (
                (
                    "la projection utilisateur "
                    "reste en watch"
                ),
                assessment["decision"] == "watch",
            ),
            (
                (
                    "une justification est "
                    "disponible"
                ),
                bool(assessment["reason"]),
            ),
            (
                (
                    "une action suivante est "
                    "disponible"
                ),
                bool(
                    assessment[
                        "recommended_action"
                    ]
                ),
            ),
            (
                (
                    "les KO restent visibles "
                    "dans les faits"
                ),
                (
                    "dns.query: KO"
                    in outcome.facts
                    and "network.ping: KO"
                    in outcome.facts
                ),
            ),
            (
                (
                    "aucun job IA n'est créé "
                    "sans Katsuyu"
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
                "sondes": len(
                    investigation_events
                ),
                "statuts": ", ".join(statuses),
                "erreurs": ", ".join(
                    str(error)
                    for error in errors
                ),
                "secret présent": (
                    "OUI"
                    if incident_has_secret
                    else "NON"
                ),
                "expertise": outcome.status,
                "décision": outcome.decision,
                "incident": updated.state,
                "confirmations sonde": len(
                    confirmed
                ),
                "jobs IA créés": (
                    ai_after - ai_before
                ),
            },
        }