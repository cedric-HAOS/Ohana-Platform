from __future__ import annotations

from ohana_agent.tsunade.incident_summary import (
    incident_assessment,
)

from scenarios._support import (
    authorize,
    diagnostic_count,
    environment,
    job_counts,
    propose,
)


def run() -> dict:
    with environment() as s:
        # Katsuyu existe initialement et fonctionne :
        # il réalise le premier travail IA.
        propose(s)

        request = authorize(s)

        target = s.jobs.latest_for_incident(
            "logs.investigate",
            str(s.incident.incident_id),
        )

        if target is None:
            raise AssertionError(
                "Le job logs.investigate attendu "
                "n'a pas été créé."
            )

        counts_before = job_counts(s)
        diagnostics_before = diagnostic_count(s)

        # -------------------------------------------------
        # Étape 1 : Katsuyu disparaît.
        #
        # Aucun nouveau poll du worker.
        # Après 30 secondes, le job doit être explicitement
        # WAITING_WORKER et le worker UNAVAILABLE.
        # -------------------------------------------------

        s.clock.advance(seconds=31)

        waiting = s.jobs.get(
            str(target.job_id)
        )

        worker = s.jobs.worker_availability(
            "sandbox-worker"
        )

        # Une consultation doit rester possible.
        listed = s.service.list_incidents()

        diagnostics_waiting = diagnostic_count(s)

        followup_waiting = (
            s.incidents.get_followup(
                str(request.request_id)
            )
        )

        waiting_checks = [
            (
                (
                    "Katsuyu devient indisponible "
                    "sans polling"
                ),
                worker.availability.value
                == "UNAVAILABLE",
            ),
            (
                (
                    "le job attend explicitement "
                    "un worker"
                ),
                waiting.status.value
                == "WAITING_WORKER",
            ),
            (
                (
                    "le suivi n'est pas encore "
                    "déclaré en échec"
                ),
                followup_waiting["status"]
                != "failed",
            ),
            (
                (
                    "Tsunade continue à exposer "
                    "les incidents"
                ),
                len(listed) >= 1,
            ),
            (
                (
                    "l'absence de Katsuyu ne crée "
                    "aucun diagnostic équipement"
                ),
                diagnostics_waiting
                == diagnostics_before,
            ),
            (
                (
                    "aucun travail supplémentaire "
                    "n'est créé"
                ),
                job_counts(s) == counts_before,
            ),
        ]

        # -------------------------------------------------
        # Étape 2 : Katsuyu reste absent jusqu'au timeout.
        #
        # On dépasse volontairement l'échéance du job.
        # Une simple lecture doit réconcilier le TIMEOUT.
        # -------------------------------------------------

        s.clock.advance(
            seconds=target.timeout + 1
        )

        s.service.list_incidents()

        expired = s.jobs.get(
            str(target.job_id)
        )

        followup = s.incidents.get_followup(
            str(request.request_id)
        )

        incident = s.incidents.get(
            s.incident.incident_id
        )

        assessment = incident_assessment(
            incident
        )

        pending = s.jobs.pending_completions(
            failures_only=True
        )

        counts_after = job_counts(s)

        timeout_checks = [
            (
                (
                    "le job expire si Katsuyu "
                    "ne revient pas"
                ),
                expired.status.value
                == "TIMEOUT",
            ),
            (
                (
                    "le suivi passe alors "
                    "à failed"
                ),
                followup["status"] == "failed",
            ),
            (
                (
                    "Tsunade distingue une "
                    "investigation interrompue"
                ),
                (
                    assessment["state"]
                    == "incomplete"
                    and assessment["label"]
                    == "Investigation interrompue"
                ),
            ),
            (
                (
                    "l'incident surveillé "
                    "reste actif"
                ),
                incident.state == "active",
            ),
            (
                (
                    "aucun résultat terminal "
                    "ne reste orphelin"
                ),
                len(pending) == 0,
            ),
            (
                (
                    "aucune relance automatique "
                    "n'est déclenchée"
                ),
                counts_after == counts_before,
            ),
        ]

        checks = (
            waiting_checks
            + timeout_checks
        )

        return {
            "passed": all(
                passed for _, passed in checks
            ),
            "checks": checks,
            "details": {
                "worker": (
                    worker.availability.value
                ),
                "avant expiration": (
                    waiting.status.value
                ),
                "après expiration": (
                    expired.status.value
                ),
                "jobs IA": (
                    counts_after["ai.inference"]
                ),
                "jobs logs": (
                    counts_after[
                        "logs.investigate"
                    ]
                ),
                "suivi": followup["status"],
                "état Tsunade": (
                    assessment["state"]
                ),
                "libellé": (
                    assessment["label"]
                ),
            },
        }