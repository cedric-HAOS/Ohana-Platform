from __future__ import annotations

from ohana_agent.tsunade.incident_summary import incident_assessment

from scenarios._support import (
    authorize,
    diagnostic_count,
    environment,
    job_counts,
    propose,
    restart,
)


def run() -> dict:
    checks = []
    details = {}
    for processed_before_restart in (False, True):
        case = (
            "échéance pendant l'arrêt"
            if not processed_before_restart
            else "échec déjà traité"
        )
        with environment() as s:
            propose(s)
            request = authorize(s)
            target = s.jobs.latest_for_incident(
                "logs.investigate", str(s.incident.incident_id)
            )
            assert target is not None, "Collecte complémentaire absente"
            counts = job_counts(s)
            original = s.incidents.get(s.incident.incident_id)
            original_events = {
                event.event_id: event.model_dump(mode="json")
                for event in original.events
            }

            if processed_before_restart:
                s.clock.advance(seconds=target.timeout + 31)
                s.service.list_incidents()
            diagnostics = diagnostic_count(s)
            restart(
                s,
                downtime_seconds=0 if processed_before_restart else target.timeout + 31,
            )
            s.service.list_incidents()
            incident = s.incidents.get(s.incident.incident_id)
            followup = s.incidents.get_followup(str(request.request_id))
            assessment = incident_assessment(incident)
            expired = s.jobs.get(str(target.job_id))
            worker = s.jobs.worker_availability("sandbox-worker")
            after_count = diagnostic_count(s)
            checks.extend(
                [
                    (
                        f"{case} : worker toujours absent",
                        worker.availability.value == "UNAVAILABLE",
                    ),
                    (f"{case} : même job expiré", expired.status.value == "TIMEOUT"),
                    (
                        f"{case} : suivi explicitement terminé",
                        followup["status"] == "failed",
                    ),
                    (f"{case} : incident actif conservé", incident.state == "active"),
                    (
                        f"{case} : preuves historiques conservées",
                        all(
                            original_events[event.event_id]
                            == event.model_dump(mode="json")
                            for event in incident.events
                            if event.event_id in original_events
                        )
                        and original_events.keys()
                        <= {event.event_id for event in incident.events},
                    ),
                    (
                        f"{case} : interruption visible",
                        assessment["state"] == "incomplete"
                        and assessment["label"] == "Investigation interrompue",
                    ),
                    (
                        f"{case} : aucun résultat orphelin",
                        not s.jobs.pending_completions(failures_only=True),
                    ),
                    (f"{case} : aucun job supplémentaire", job_counts(s) == counts),
                    (
                        f"{case} : aucune conclusion équipement inventée",
                        after_count == diagnostics,
                    ),
                ]
            )

            # Une deuxième reconstruction complète doit conserver l'état terminal.
            event_count = len(incident.events)
            restart(s)
            for _ in range(3):
                s.service.list_incidents()
            restored = s.incidents.get(s.incident.incident_id)
            checks.extend(
                [
                    (
                        f"{case} : lectures et seconde reprise idempotentes",
                        len(restored.events) == event_count
                        and diagnostic_count(s) == after_count,
                    ),
                    (
                        f"{case} : aucune relance après seconde reprise",
                        job_counts(s) == counts,
                    ),
                ]
            )
            details[case] = (
                f"{expired.status.value}, {followup['status']}, {assessment['label']}"
            )
    return {
        "passed": all(passed for _, passed in checks),
        "checks": checks,
        "details": details,
    }
