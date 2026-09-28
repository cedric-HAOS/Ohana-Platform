"""Incident pages stay readable while a Katsuyu result is being processed.

Production, 28 September 12:09–12:12: Vision answered 502 sixteen times on
the Tsunade incident list. Processing one logs.health_check result (four log
reviews, about 2.4 s per write on the INFRA-01 SD card) held the Agent's
worker cycle lock for 38 s, then each AI result held it again. Every page
read first settled the job queue under that same lock and waited past
Vision's 10 s timeout. Shizune's summary and requests waited the same way.

Here recording the log review takes 3 s: reads must answer within 1 s and
the completion must still be processed.
"""

from __future__ import annotations

import threading
import time
from datetime import timedelta

from ohana_katsuyu.handlers import HandlerContext, LogsHealthCheckHandler

from scenarios._support import environment

WORKER = "sandbox-worker"
SLOW_WRITE_SECONDS = 3.0
READ_BUDGET_SECONDS = 1.0


def _lines(now) -> list[str]:
    # Zone-less Paris wall-clock text, exactly as Home Assistant writes it.
    stamp = (now - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    return [
        f"{stamp} ERROR (MainThread) [kasa.smart.smartdevice] "
        "Error querying 192.168.1.44 for modules"
    ] * 3


def _claim_check(s):
    s.service.request_log_health_check(now=s.clock(), max_bytes=65536, window_hours=24)
    claimed = s.service.next_worker_job(
        {"worker_id": WORKER, "supported_types": ["logs.health_check"]}
    ).job
    assert claimed is not None and claimed.type == "logs.health_check"
    lines = _lines(s.clock())

    def source_provider(job_id, worker_id, attempt, source):
        return {"source": source, "transport": "inline", "content": "\n".join(lines)}

    result = LogsHealthCheckHandler(source_provider).execute(
        claimed.parameters,
        HandlerContext(job_id=str(claimed.job_id), worker_id=WORKER, attempt=1),
    )
    payload = {
        "worker_id": WORKER,
        "attempt": claimed.attempt,
        "status": "SUCCEEDED",
        "result": result,
    }
    return claimed, payload


def _timed(operation) -> float:
    started = time.monotonic()
    operation()
    return time.monotonic() - started


def run() -> dict:
    checks = []
    details = {}
    with environment() as s:
        s.jobs.register_worker(
            {
                "worker_id": WORKER,
                "platform": "Sandbox",
                "worker_version": "dev",
                "capabilities": ["logs.health_check"],
            }
        )
        claimed, payload = _claim_check(s)
        s.service.complete_job(str(claimed.job_id), payload)
        incident = next(
            item for item in s.incidents.list() if item.capability_id == "logs.health"
        )

        # Next check: its log review is written as slowly as on the SD card.
        claimed, payload = _claim_check(s)
        inside = threading.Event()
        record_log_health = s.incidents.record_log_health

        def slow_record(*args, **kwargs):
            inside.set()
            time.sleep(SLOW_WRITE_SECONDS)
            return record_log_health(*args, **kwargs)

        s.incidents.record_log_health = slow_record
        completion = threading.Thread(
            target=s.service.complete_job, args=(str(claimed.job_id), payload)
        )
        completion.start()
        assert inside.wait(5), "le traitement du résultat n'a pas commencé"
        reads = {
            "liste des incidents": lambda: s.service.list_incidents("all"),
            "détail d'un incident": lambda: s.service.read_incident(
                str(incident.incident_id)
            ),
            "synthèse Shizune": s.service.read_companion_summary,
            "demandes Shizune": s.service.read_companion_requests,
        }
        timings: dict[str, float] = {}
        # Pages are read concurrently, as Vision and Shizune do.
        readers = [
            threading.Thread(
                target=lambda name=name, read=read: timings.__setitem__(
                    name, _timed(read)
                )
            )
            for name, read in reads.items()
        ]
        for reader in readers:
            reader.start()
        for reader in readers:
            reader.join(10)
        completion.join(10)
        s.incidents.record_log_health = record_log_health
        for name in reads:
            seconds = timings.get(name, float("inf"))
            details[name] = f"{seconds:.2f} s"
            checks.append(
                (
                    f"{name} lue en moins de {READ_BUDGET_SECONDS:.0f} s pendant "
                    "le traitement d'un résultat",
                    seconds < READ_BUDGET_SECONDS,
                )
            )
        checks.append(
            (
                "le résultat est quand même traité : plus rien en attente",
                not completion.is_alive()
                and not s.jobs.pending_completions()
                and s.incidents.get(incident.incident_id).last_observation_id
                == claimed.job_id,
            )
        )
    details["portée"] = "Agent, Tsunade et analyseur Katsuyu locaux ; aucun accès production"
    details["limites"] = "Écriture lente simulée par une attente de 3 s"
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
