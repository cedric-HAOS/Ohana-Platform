from __future__ import annotations

import json
from datetime import datetime

from ohana_agent.tsunade.incident_summary import incident_assessment

from scenarios._support import (
    ai_result,
    authorize,
    environment,
    job_counts,
    poll,
    propose,
    restart,
)


def run() -> dict:
    checks = []
    details = {}
    for matches, truncated in ((0, False), (239, False), (239, True)):
        case = f"{matches} lignes, truncated={truncated}"
        with environment() as s:
            propose(s)
            checks.append(
                (
                    f"{case} : aucune collecte avant autorisation",
                    s.jobs.count("logs.investigate") == 0,
                )
            )
            request = authorize(s)
            collection = poll(s)
            assert collection is not None and collection.type == "logs.investigate"
            collection_result = {
                "worker_id": "sandbox-worker",
                "attempt": collection.attempt,
                "status": "SUCCEEDED",
                "result": {
                    "status": "OK",
                    "analyzed_at": s.clock().isoformat(),
                    "source": "ha-01",
                    "pattern": "timeout",
                    "matched_lines": matches,
                    "findings": [],
                    "truncated": truncated,
                },
            }
            s.service.complete_job(str(collection.job_id), collection_result)
            review = poll(s)
            assert review is not None and review.type == "ai.inference"
            evidence = {
                item["source"]: json.loads(item["content"])
                for item in review.parameters["evidence"]
            }
            original = evidence["logs.analysis"]["findings"]
            targeted = evidence["investigation.followup"]
            checks.extend(
                [
                    (
                        f"{case} : anomalies initiales préservées",
                        len(original) == len(s.incident.context["findings"])
                        and all(
                            all(
                                actual.get(key) == value
                                for key, value in expected.items()
                            )
                            for actual, expected in zip(
                                original, s.incident.context["findings"], strict=True
                            )
                        ),
                    ),
                    (
                        f"{case} : aucune date inventée pour les anomalies",
                        all(
                            item.get("first_at") is None and item.get("last_at") is None
                            for item in original
                        ),
                    ),
                    (
                        f"{case} : collecte séparée et fidèle",
                        targeted["result"]
                        == {**collection_result["result"], "finding_count": 0},
                    ),
                    (
                        f"{case} : cible et fenêtre conservées",
                        targeted["scope"] == collection.parameters,
                    ),
                    (
                        f"{case} : observation de référence conservée",
                        datetime.fromisoformat(
                            evidence["shikamaru.observation"]["last_observed_at"]
                        )
                        == s.incident.last_observed_at,
                    ),
                ]
            )
            # Une réponse volontairement contraire au booléen de collecte ne
            # doit pas devenir le motif déterministe de la décision Tsunade.
            result = ai_result()
            result["summary"] = (
                "Collecte non tronquée." if truncated else "Collecte tronquée."
            )
            completion = {
                "worker_id": "sandbox-worker",
                "attempt": review.attempt,
                "status": "SUCCEEDED",
                "result": result,
            }
            s.service.complete_job(str(review.job_id), completion)
            incident = s.incidents.get(s.incident.incident_id)
            assessment = incident_assessment(incident)
            diagnostic = [
                event.payload for event in incident.events if event.kind == "diagnostic"
            ][-1]
            facts = diagnostic.get("collection_facts") or {}
            expected_wording = (
                "Collecte tronquée." if truncated else "Collecte non tronquée."
            )
            checks.extend(
                [
                    (
                        f"{case} : lignes distinctes des anomalies",
                        facts.get("matched_lines") == matches
                        and facts.get("anomaly_count") == 0,
                    ),
                    (
                        f"{case} : troncature factuelle conservée",
                        facts.get("truncated") is truncated,
                    ),
                    (
                        f"{case} : motif fondé sur la collecte",
                        expected_wording in (assessment["reason"] or ""),
                    ),
                    (
                        f"{case} : incident non clôturé par la collecte vide",
                        incident.state == "active",
                    ),
                    (
                        f"{case} : terminaison explicite sans cause inventée",
                        assessment["state"] == "investigation_exhausted"
                        and assessment["decision"] == "watch"
                        and assessment["diagnostic_level"] == "INSUFFICIENT_CONTEXT",
                    ),
                    (
                        f"{case} : suivi incomplet et action lisible",
                        incident.followup["status"] == "incomplete"
                        and assessment["next_action"] == "details",
                    ),
                    (
                        f"{case} : cycle borné à deux IA et une collecte",
                        job_counts(s) == {"ai.inference": 2, "logs.investigate": 1},
                    ),
                ]
            )
            persisted_events = [
                event.model_dump(mode="json") for event in incident.events
            ]
            # Livraison répétée, puis reconstruction complète depuis SQLite.
            s.service.complete_job(str(collection.job_id), collection_result)
            s.service.complete_job(str(review.job_id), completion)
            restart(s)
            for _ in range(3):
                s.service.list_incidents()
            restored = s.incidents.get(s.incident.incident_id)
            checks.extend(
                [
                    (
                        f"{case} : événements identiques après doublons et reprise",
                        [event.model_dump(mode="json") for event in restored.events]
                        == persisted_events,
                    ),
                    (
                        f"{case} : projection persistée identique",
                        incident_assessment(restored) == assessment,
                    ),
                    (f"{case} : aucun nouveau travail disponible", poll(s) is None),
                    (
                        f"{case} : aucune nouvelle autorisation",
                        not s.service.read_companion_requests().requests,
                    ),
                    (
                        f"{case} : aucun résultat non traité",
                        not s.jobs.pending_completions(),
                    ),
                    (
                        f"{case} : aucune relance persistée",
                        job_counts(s) == {"ai.inference": 2, "logs.investigate": 1}
                        and s.incidents.get_followup(str(request.request_id))["status"]
                        == "incomplete",
                    ),
                ]
            )
            details[case] = (
                f"{assessment['state']}, {assessment['decision']}, 2 IA simulées / 1 collecte"
            )
    return {
        "passed": all(passed for _, passed in checks),
        "checks": checks,
        "details": details,
    }
