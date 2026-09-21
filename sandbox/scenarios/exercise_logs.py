"""Local cross-repository log pipeline; only the log source is supplied by the lab."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ohana_katsuyu.handlers import HandlerContext, LogsHealthCheckHandler

from scenarios._support import environment, restart


def run(*, logs_file: Path | None = None, window_end: str | None = None) -> dict:
    checks = []
    details = {}
    # Unknown real input has no expected health verdict. PASS means the pipeline
    # processed it faithfully, not that the journal contains no anomalies.
    cases = (
        [("fichier local", logs_file.read_text(encoding="utf-8"), None)]
        if logs_file
        else [
            ("journal sain", "INFO Service ready\n", "OK"),
            ("anomalie", "ERROR Connection timeout\n" * 2, "KO"),
            ("collecte bornée", "INFO Service ready\n" * 1000, "OK"),
        ]
    )
    for label, content, expected in cases:
        with environment() as s:
            if window_end:
                current = datetime.fromisoformat(window_end)
                if current.tzinfo is None or current.utcoffset() is None:
                    raise ValueError("--window-end exige un fuseau horaire")
                s.clock.current = current
            s.jobs.register_worker(
                {
                    "worker_id": "sandbox-worker",
                    "platform": "Sandbox",
                    "worker_version": "dev",
                    "capabilities": ["logs.health_check"],
                }
            )
            requested = s.service.request_log_health_check(
                now=s.clock(), max_bytes=4096
            )
            claimed = s.service.next_worker_job(
                {
                    "worker_id": "sandbox-worker",
                    "supported_types": ["logs.health_check"],
                }
            ).job
            assert claimed is not None and claimed.type == "logs.health_check"

            def source_provider(
                job_id, worker_id, attempt, source, claimed=claimed, content=content
            ):
                assert (job_id, worker_id, attempt, source) == (
                    str(claimed.job_id),
                    "sandbox-worker",
                    claimed.attempt,
                    "ha-01",
                )
                return {"source": source, "transport": "inline", "content": content}

            result = LogsHealthCheckHandler(source_provider).execute(
                claimed.parameters,
                HandlerContext(
                    job_id=str(claimed.job_id),
                    worker_id="sandbox-worker",
                    attempt=claimed.attempt,
                ),
            )
            completion = {
                "worker_id": "sandbox-worker",
                "attempt": claimed.attempt,
                "status": "SUCCEEDED",
                "result": result,
            }
            s.service.complete_job(str(claimed.job_id), completion)
            projection = s.service.list_incidents()
            incidents = [
                s.incidents.get(i.incident_id).model_dump(mode="json")
                for i in s.incidents.list(state="all")
            ]
            checks.extend(
                [
                    (
                        f"{label} : job demandé puis pris en charge",
                        str(requested.job_id) == str(claimed.job_id),
                    ),
                    (
                        f"{label} : résultat Katsuyu traité par Agent",
                        s.jobs.get(str(claimed.job_id)).status.value == "SUCCEEDED"
                        and not s.jobs.pending_completions(),
                    ),
                    (
                        f"{label} : résultat disponible dans la projection pour Vision",
                        projection["log_health"]["result"] == result,
                    ),
                    (
                        f"{label} : limite de collecte préservée",
                        result["sources"][0]["fetched_bytes"] <= 4096
                        and (
                            len(content.encode("utf-8")) <= 4096
                            or result["sources"][0]["truncated"]
                        ),
                    ),
                    (
                        f"{label} : verdict attendu",
                        expected is None or result["status"] == expected,
                    ),
                ]
            )
            if expected == "KO":
                checks.append(
                    (
                        f"{label} : preuves transmises à Tsunade",
                        any(
                            i.context.get("findings")
                            == result["sources"][0]["findings"]
                            and any(
                                e.payload.get("job_id") == str(claimed.job_id)
                                for e in s.incidents.get(i.incident_id).events
                            )
                            for i in s.incidents.list()
                        ),
                    )
                )
            s.service.complete_job(str(claimed.job_id), completion)
            restart(s)
            checks.extend(
                [
                    (
                        f"{label} : preuves conservées après doublon et reprise",
                        [
                            s.incidents.get(i.incident_id).model_dump(mode="json")
                            for i in s.incidents.list(state="all")
                        ]
                        == incidents,
                    ),
                    (
                        f"{label} : projection conservée après reprise",
                        s.service.list_incidents()["log_health"]
                        == projection["log_health"],
                    ),
                    (
                        f"{label} : aucun contrôle relancé",
                        s.jobs.count("logs.health_check") == 1
                        and s.jobs.active_for_incident("logs.health_check", None)
                        is None,
                    ),
                ]
            )
            details[label] = (
                f"{result['status']}, "
                f"{result['sources'][0]['analyzed_lines']} lignes analysées, "
                f"{len(result['sources'][0]['findings'])} anomalies groupées"
            )
    details["portée"] = (
        "Sources locales Agent/Katsuyu ; entrée locale ; aucun accès production"
    )
    details["limites"] = (
        "Sans transport HTTP, boucle worker, modèle IA ou rendu navigateur Vision"
    )
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
