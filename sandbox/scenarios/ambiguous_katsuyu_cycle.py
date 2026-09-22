from __future__ import annotations

from datetime import timedelta

from ohana_agent.tsunade.incident_summary import (
    incident_assessment,
)

from scenarios._support import environment


SENSOR = "sensor.pool_temperature"


def _log_result(now):
    first = now - timedelta(minutes=2)
    last = now - timedelta(minutes=1)

    return {
        "status": "KO",
        "analyzed_at": now.isoformat(),
        "window_started_at": (
            now - timedelta(hours=1)
        ).isoformat(),
        "window_ended_at": now.isoformat(),
        "sources": [
            {
                "source": "ha-01",
                "status": "KO",
                "fetched_bytes": 1400,
                "truncated": False,
                "analyzed_lines": 24,
                "findings": [
                    {
                        "source": "ha-01",
                        "signature": (
                            "error templateerror: float got "
                            "invalid input unavailable for "
                            "sensor.pool_temperature"
                        ),
                        "category": "other",
                        "severity": "error",
                        "summary": (
                            "Template float impossible pour "
                            "sensor.pool_temperature."
                        ),
                        "references": [SENSOR],
                        "occurrences": 1,
                        "reference_occurrences": None,
                        "first_at": first.isoformat(),
                        "last_at": last.isoformat(),
                        "trend": "new",
                    },
                    {
                        "source": "ha-01",
                        "signature": (
                            "error rendering template for "
                            "sensor.pool_temperature"
                        ),
                        "category": "other",
                        "severity": "error",
                        "summary": (
                            "Erreur de rendu du template lié à "
                            "sensor.pool_temperature."
                        ),
                        "references": [SENSOR],
                        "occurrences": 1,
                        "reference_occurrences": None,
                        "first_at": first.isoformat(),
                        "last_at": last.isoformat(),
                        "trend": "new",
                    },
                ],
            }
        ],
        "new_anomaly_count": 2,
        "worsening_anomaly_count": 0,
        "disappeared_anomalies": [],
        "correlations": [],
        "recommended_investigations": [
            (
                "Vérifier l'état courant de "
                "sensor.pool_temperature."
            )
        ],
    }


def _ai_result(now):
    return {
        "analysis_version": 2,
        "verdict": "KO",
        "generated_at": now.isoformat(),
        "model_id": "sandbox-ambiguous",
        "model_sha256": "a" * 64,
        "interpretation": (
            "Les journaux montrent une erreur de template "
            "lors de la conversion float de "
            "sensor.pool_temperature. Ils sont compatibles "
            "avec une valeur temporairement unavailable, "
            "mais ne permettent pas d'établir la cause de "
            "cette indisponibilité."
        ),
        "summary": (
            "Une erreur de template est probablement la "
            "conséquence d'un état non numérique de l'entité, "
            "sans preuve suffisante sur la cause initiale."
        ),
        "findings": [
            {
                "code": "HA.TEMPLATE.FLOAT",
                "evidence": (
                    "Le filtre float a reçu une valeur "
                    "non numérique pour "
                    "sensor.pool_temperature."
                ),
                "confidence": 0.90,
            }
        ],
        "hypotheses": [
            {
                "statement": (
                    "L'erreur de template float est compatible "
                    "avec un état temporairement unavailable de "
                    "sensor.pool_temperature, mais cela "
                    "n'explique pas pourquoi l'entité était "
                    "indisponible."
                ),
                "confidence": 0.82,
                "possible_causes": [
                    "indisponibilité temporaire du capteur",
                    "template sans valeur float par défaut",
                ],
                "supporting_evidence": [
                    (
                        "le journal mentionne une erreur "
                        "de conversion float"
                    ),
                    (
                        "sensor.pool_temperature est "
                        "explicitement référencé"
                    ),
                ],
                "contradicting_evidence": [
                    (
                        "l'état courant de l'entité "
                        "n'a pas été vérifié"
                    ),
                    (
                        "aucune preuve directe du capteur "
                        "n'établit la cause"
                    ),
                ],
            }
        ],
        "missing_context": [
            (
                "État courant de "
                "sensor.pool_temperature."
            ),
            (
                "Cause de son éventuelle indisponibilité."
            ),
        ],
        "recommended_investigation": [
            (
                "Vérifier dans un modèle Home Assistant "
                "l'état courant de sensor.pool_temperature "
                "et sa conversion float, sans modifier "
                "la configuration."
            )
        ],
        "metrics": {
            "prompt_tokens": 100,
            "completion_tokens": 100,
            "ttft_ms": 1,
            "tokens_per_second": 20,
            "duration_seconds": 5,
        },
    }


def _claim_log_job(s):
    response = s.service.next_worker_job(
        {
            "worker_id": "sandbox-log-worker",
            "supported_types": [
                "logs.health_check",
            ],
        }
    )

    assert response.job is not None
    assert response.job.type == "logs.health_check"

    return response.job


def run() -> dict:
    with environment() as s:
        checks = []

        s.jobs.register_worker(
            {
                "worker_id": "sandbox-log-worker",
                "platform": "Sandbox",
                "worker_version": "dev",
                "capabilities": [
                    "logs.health_check",
                ],
            }
        )

        # ==============================================
        # 1. Une vraie anomalie logs arrive dans Agent
        # ==============================================

        requested = s.service.request_log_health_check(
            now=s.clock(),
            max_bytes=4096,
        )

        log_job = _claim_log_job(s)

        assert str(requested.job_id) == str(log_job.job_id)

        result = _log_result(s.clock())

        s.service.complete_job(
            str(log_job.job_id),
            {
                "worker_id": "sandbox-log-worker",
                "attempt": log_job.attempt,
                "status": "SUCCEEDED",
                "result": result,
            },
        )

        incident = next(
            incident
            for incident in s.incidents.list()
            if incident.node_id == "ha-01"
            and incident.capability_id == "logs.health"
        )

        incident = s.incidents.get(
            incident.incident_id
        )

        # Agent doit avoir escaladé automatiquement.
        ai_job = s.jobs.latest_for_incident(
            "ai.inference",
            str(incident.incident_id),
        )

        queued_diagnostics = [
            event
            for event in incident.events
            if event.kind == "diagnostic"
            and event.payload.get("cycle_status")
            == "ai_queued"
        ]

        checks.extend(
            [
                (
                    "incident logs.health actif",
                    incident.state == "active",
                ),
                (
                    "deux anomalies nouvelles conservées",
                    (
                        len(
                            incident.context.get(
                                "findings",
                                [],
                            )
                        )
                        == 2
                        and all(
                            finding.get("trend") == "new"
                            for finding in incident.context.get(
                                "findings",
                                [],
                            )
                        )
                    ),
                ),
                (
                    (
                        "Tsunade demande automatiquement "
                        "Katsuyu"
                    ),
                    ai_job is not None,
                ),
                (
                    (
                        "l'escalade est justifiée par "
                        "l'insuffisance déterministe"
                    ),
                    (
                        len(queued_diagnostics) == 1
                        and queued_diagnostics[0]
                        .payload.get("trigger")
                        == "automatic_escalation"
                    ),
                ),
                (
                    (
                        "aucune action corrective n'est "
                        "autorisée avant Katsuyu"
                    ),
                    not any(
                        event.kind == "diagnostic"
                        and event.payload.get(
                            "decision"
                        )
                        == "action_required"
                        for event in incident.events
                    ),
                ),
            ]
        )

        assert ai_job is not None

        evidence = ai_job.parameters["evidence"]

        checks.append(
            (
                "la preuve IA contient les journaux bornés",
                any(
                    item["source"] == "logs.analysis"
                    and SENSOR in item["content"]
                    for item in evidence
                ),
            )
        )

        # ==============================================
        # 2. Katsuyu analyse l'ambiguïté
        # ==============================================

        claimed_ai = s.service.next_worker_job(
            {
                "worker_id": "sandbox-worker",
                "supported_types": [
                    "ai.inference",
                ],
            }
        ).job

        assert claimed_ai is not None
        assert str(claimed_ai.job_id) == str(
            ai_job.job_id
        )

        s.service.complete_job(
            str(claimed_ai.job_id),
            {
                "worker_id": "sandbox-worker",
                "attempt": claimed_ai.attempt,
                "status": "SUCCEEDED",
                "result": _ai_result(s.clock()),
            },
        )

        diagnosed = s.incidents.get(
            incident.incident_id
        )

        assessment = incident_assessment(
            diagnosed
        )

        ai_diagnostic = [
            event
            for event in diagnosed.events
            if event.kind == "diagnostic"
            and event.payload.get("cycle_status")
            == "ai_completed"
        ][-1]

        ai_actions = [
            event
            for event in diagnosed.events
            if event.kind == "action"
            and event.payload.get("origin")
            == "katsuyu_ai"
        ]

        commands = (
            ai_actions[-1].payload.get(
                "investigation_commands",
                [],
            )
            if ai_actions
            else []
        )

        checks.extend(
            [
                (
                    "Katsuyu reste une hypothèse",
                    (
                        ai_diagnostic.payload.get(
                            "epistemic_status"
                        )
                        == "hypothesis"
                    ),
                ),
                (
                    "diagnostic final PROBABLE",
                    (
                        assessment[
                            "diagnostic_level"
                        ]
                        == "PROBABLE"
                    ),
                ),
                (
                    (
                        "Tsunade conserve une décision "
                        "investigate"
                    ),
                    (
                        assessment["decision"]
                        == "investigate"
                    ),
                ),
                (
                    (
                        "une hypothèse Katsuyu ne devient "
                        "jamais action_required"
                    ),
                    (
                        assessment["decision"]
                        != "action_required"
                    ),
                ),
                (
                    (
                        "les éléments manquants pour "
                        "confirmer sont visibles"
                    ),
                    bool(
                        assessment[
                            "confirmation_gap"
                        ]
                    ),
                ),
                (
                    (
                        "l'investigation proposée reste "
                        "en lecture seule"
                    ),
                    any(
                        command.get("safety")
                        == "Lecture seule"
                        and SENSOR
                        in command.get(
                            "command",
                            "",
                        )
                        for command in commands
                    ),
                ),
            ]
        )

        # ==============================================
        # 3. Même preuve : pas de boucle IA
        # ==============================================

        initial_ai_count = s.jobs.count(
            "ai.inference"
        )

        second_requested = (
            s.service.request_log_health_check(
                now=s.clock(),
                max_bytes=4096,
            )
        )

        second_log_job = _claim_log_job(s)

        assert (
            str(second_requested.job_id)
            == str(second_log_job.job_id)
        )

        second_result = {
            **result,
            "analyzed_at": (
                s.clock()
                + timedelta(minutes=1)
            ).isoformat(),
        }

        s.service.complete_job(
            str(second_log_job.job_id),
            {
                "worker_id": "sandbox-log-worker",
                "attempt": second_log_job.attempt,
                "status": "SUCCEEDED",
                "result": second_result,
            },
        )

        after_repeat = s.incidents.get(
            incident.incident_id
        )

        checks.extend(
            [
                (
                    (
                        "la même preuve ne crée pas "
                        "une seconde IA"
                    ),
                    (
                        s.jobs.count(
                            "ai.inference"
                        )
                        == initial_ai_count
                    ),
                ),
                (
                    (
                        "le même incident est conservé"
                    ),
                    (
                        after_repeat.incident_id
                        == incident.incident_id
                    ),
                ),
            ]
        )

        return {
            "passed": all(
                passed for _, passed in checks
            ),
            "checks": checks,
            "details": {
                "incident": str(
                    incident.incident_id
                ),
                "niveau": assessment[
                    "diagnostic_level"
                ],
                "décision": assessment[
                    "decision"
                ],
                "jobs IA": s.jobs.count(
                    "ai.inference"
                ),
                "commande lecture seule": (
                    commands[0]["command"]
                    if commands
                    else "absente"
                ),
            },
        }