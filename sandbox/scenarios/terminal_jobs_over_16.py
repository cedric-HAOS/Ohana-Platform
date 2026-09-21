from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

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
        propose(s)
        request = authorize(s)

        target = s.jobs.latest_for_incident(
            "logs.investigate",
            str(s.incident.incident_id),
        )

        if target is None:
            raise AssertionError(
                "Le job de collecte autorisé est absent."
            )

        created_at = s.clock()

        for index in range(16):
            dummy = s.jobs.create(
                {
                    "protocol_version": 1,
                    "job_id": str(uuid4()),
                    "type": "logs.investigate",
                    "created_at": (
                        created_at.isoformat()
                    ),
                    "parameters": {
                        "source": "ha-01",
                        "pattern": f"dummy-{index}",
                        "window_started_at": (
                            created_at
                            - timedelta(hours=2)
                        ).isoformat(),
                        "window_ended_at": (
                            created_at.isoformat()
                        ),
                        "max_bytes": (
                            s.service.log_max_bytes
                        ),
                        "incident_id": str(uuid4()),
                    },
                    "timeout": (
                        s.service.log_timeout_seconds
                    ),
                }
            )

            s.jobs.cancel(str(dummy.job_id))

        counts_before = job_counts(s)

        s.clock.advance(days=1)

        s.service.list_incidents()

        expired = s.jobs.get(
            str(target.job_id)
        )

        followup = s.incidents.get_followup(
            str(request.request_id)
        )

        current = s.incidents.get(
            s.incident.incident_id
        )

        assessment = incident_assessment(current)

        pending = s.jobs.pending_completions(
            failures_only=True
        )

        event_count = len(current.events)

        s.service.list_incidents()

        second = s.incidents.get(
            s.incident.incident_id
        )

        counts_after = job_counts(s)

        checks = [
            (
                "le job réel expire sans polling Katsuyu",
                expired.status.value == "TIMEOUT",
            ),
            (
                "le suivi utilisateur passe à failed",
                followup["status"] == "failed",
            ),
            (
                (
                    "l'incident devient "
                    "« Investigation interrompue »"
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
                    "les 17 résultats terminaux "
                    "sont réconciliés"
                ),
                len(pending) == 0,
            ),
            (
                "aucun travail n'est relancé",
                counts_after == counts_before,
            ),
            (
                (
                    "une seconde consultation "
                    "est idempotente"
                ),
                len(second.events) == event_count,
            ),
        ]

        return {
            "passed": all(
                passed for _, passed in checks
            ),
            "checks": checks,
            "details": {
                "jobs IA": (
                    counts_after["ai.inference"]
                ),
                "jobs logs": (
                    counts_after[
                        "logs.investigate"
                    ]
                ),
                "résultats en attente": len(
                    pending
                ),
                "diagnostics": diagnostic_count(s),
                "état Tsunade": (
                    assessment["state"]
                ),
                "libellé": (
                    assessment["label"]
                ),
            },
        }