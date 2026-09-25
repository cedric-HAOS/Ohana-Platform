"""Daily HA-01 log reviews through the real Katsuyu analyser.

Production, 25 September: HA-01 and LINKY-01 log incidents open since August
requested two ai.inference per day, because every daily check showed the same
anomalies with a new count and date. Home Assistant also logs zone-less
Europe/Paris times, which Katsuyu read as UTC.
"""

from __future__ import annotations

from datetime import timedelta

from ohana_katsuyu.handlers import HandlerContext, LogsHealthCheckHandler

from scenarios._support import ai_result, environment, restart

WORKER = "sandbox-worker"


def _ha_lines(now, *, minutes_ago: int, kasa: int, mqtt: int) -> list[str]:
    # Zone-less Paris wall-clock text, exactly as Home Assistant writes it.
    stamp = (now - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    return [
        f"{stamp} ERROR (MainThread) [kasa.smart.smartdevice] "
        "Error querying 192.168.1.44 for modules"
    ] * kasa + [
        f"{stamp} WARNING (MainThread) [homeassistant.components.mqtt.client] "
        "Disconnected from MQTT server core-mosquitto:1883"
    ] * mqtt


def _daily_check(s, *, window_hours: int, lines: list[str]) -> dict:
    s.service.request_log_health_check(
        now=s.clock(), max_bytes=65536, window_hours=window_hours
    )
    claimed = s.service.next_worker_job(
        {"worker_id": WORKER, "supported_types": ["logs.health_check"]}
    ).job
    assert claimed is not None and claimed.type == "logs.health_check"

    def source_provider(job_id, worker_id, attempt, source):
        return {"source": source, "transport": "inline", "content": "\n".join(lines)}

    result = LogsHealthCheckHandler(source_provider).execute(
        claimed.parameters,
        HandlerContext(job_id=str(claimed.job_id), worker_id=WORKER, attempt=1),
    )
    s.service.complete_job(
        str(claimed.job_id),
        {
            "worker_id": WORKER,
            "attempt": claimed.attempt,
            "status": "SUCCEEDED",
            "result": result,
        },
    )
    return result


def _answer_ai(s) -> bool:
    claimed = s.service.next_worker_job(
        {"worker_id": WORKER, "supported_types": ["ai.inference"]}
    ).job
    if claimed is None:
        return False
    s.service.complete_job(
        str(claimed.job_id),
        {
            "worker_id": WORKER,
            "attempt": claimed.attempt,
            "status": "SUCCEEDED",
            "result": ai_result(),
        },
    )
    return True


def _log_incident(s):
    return next(
        incident
        for incident in s.incidents.list()
        if incident.capability_id == "logs.health"
        and incident.service_id == "home-assistant"
    )


def run() -> dict:
    checks = []
    details = {}
    with environment() as s:
        s.jobs.register_worker(
            {
                "worker_id": WORKER,
                "platform": "Sandbox",
                "worker_version": "dev",
                "capabilities": ["logs.health_check", "ai.inference"],
            }
        )

        # Day 1: new anomalies, one expertise.
        first = _daily_check(
            s,
            window_hours=24,
            lines=_ha_lines(s.clock(), minutes_ago=50, kasa=3, mqtt=2),
        )
        day1_ai = s.jobs.count("ai.inference")
        checks += [
            (
                "contrôle 1 : les heures de Paris sans fuseau tombent dans la fenêtre",
                first["sources"][0]["analyzed_lines"] == 5,
            ),
            (
                "contrôle 1 : la déconnexion MQTT est une anomalie datée",
                any(
                    "disconnected from mqtt" in finding["signature"]
                    and finding["last_at"] is not None
                    for finding in first["sources"][0]["findings"]
                ),
            ),
            ("contrôle 1 : une expertise pour des anomalies nouvelles", day1_ai == 1),
            ("contrôle 1 : l'expertise simulée est traitée", _answer_ai(s)),
        ]

        # Next check (the Sandbox clock stays still: job timestamps use system
        # time). Same anomalies, new count and date, no comparable baseline
        # (different window length), as the daily production checks.
        restart(s)
        s.jobs.register_worker(
            {
                "worker_id": WORKER,
                "platform": "Sandbox",
                "worker_version": "dev",
                "capabilities": ["logs.health_check", "ai.inference"],
            }
        )
        second = _daily_check(
            s,
            window_hours=12,
            lines=_ha_lines(s.clock(), minutes_ago=40, kasa=4, mqtt=2),
        )
        decision = _log_incident(s).latest_decision or {}
        checks += [
            (
                "contrôle 2 : Katsuyu ne dispose pas de référence (tendance new)",
                {f["trend"] for f in second["sources"][0]["findings"]} == {"new"},
            ),
            (
                "contrôle 2 : aucune nouvelle expertise pour les mêmes anomalies",
                s.jobs.count("ai.inference") == 1,
            ),
            (
                "contrôle 2 : décision de surveillance",
                decision.get("decision") == "watch",
            ),
        ]

        # Last check: both rates more than double. Tsunade escalates automatically
        # only for two significant changes, a critical finding or a correlation.
        _daily_check(
            s,
            window_hours=6,
            lines=_ha_lines(s.clock(), minutes_ago=30, kasa=12, mqtt=9),
        )
        checks.append(
            (
                "contrôle 3 : une aggravation nette relance une expertise",
                s.jobs.count("ai.inference") == 2,
            )
        )
        details["expertises"] = f"{s.jobs.count('ai.inference')} sur 3 contrôles"
    details["portée"] = (
        "Agent, Tsunade et analyseur Katsuyu locaux ; aucun accès production"
    )
    details["limites"] = "Réponse IA simulée ; sans transport HTTP ni modèle"
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
