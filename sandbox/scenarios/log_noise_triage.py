"""Daily log reviews of the four sources, as they looked on 27 September.

Production: the four logs.health incidents had stayed open since August. They
mixed Ohana's own INFO lines and deployments (INFRA-01), the nightly Z-Wave
NVM backup, third-party Home Assistant errors, and two real faults drowned in
them: 2 764 refused Linky frames a day (DNS answered 127.0.1.1) and SD card
stalls. Only errors and frequent warnings may keep an incident open, and a
signature accepted as known noise must stop counting.
"""

from __future__ import annotations

from datetime import timedelta

from ohana_agent.api.service import AdministrationService
from ohana_agent.infrastructure.repository import InfrastructureConfigurationRepository
from ohana_katsuyu.handlers import HandlerContext, LogsHealthCheckHandler

from scenarios._support import environment

WORKER = "sandbox-worker"
SOURCES = ("infra-01", "ha-01", "linky-01", "zwave-01")


def _lines(now, *, dns_fixed: bool) -> dict[str, list[str]]:
    iso = (now - timedelta(minutes=30)).isoformat()
    # Zone-less Paris wall-clock text, exactly as Home Assistant writes it.
    ha = (now - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    agent = f"{iso} infra-01 ohana-agent[980629]: 2026-09-27 05:00:00,000"
    return {
        "infra-01": [
            f"{agent} INFO ohana_agent.tsunade.investigations — "
            "Investigation 1 started: zwave.status",
            f"{agent} INFO ohana_agent.runtime.agent — Ohana-Agent started.",
            f"{iso} infra-01 systemd[1]: Stopping ohana-agent.service - Ohana Agent...",
            f"{iso} infra-01 systemd[1]: Started ohana-vision.service - Ohana Vision.",
            f"{iso} infra-01 ohana-vision[980634]: INFO:     Started server process [1]",
        ]
        + [
            f"{agent} WARNING ohana_agent.observation.exporters.durable_vision_client"
            " — Unable to deliver observation 1 to Ohana-Vision: Timed out"
        ]
        * 20,
        "zwave-01": [
            f"{iso} INFO BACKUP: Backup NVM started",
            f"{iso} CNTRLR   stopping hardware watchdog...",
            f"{iso} CNTRLR   waiting for the controller to reconnect...",
            f"{iso} CNTRLR   reconnected and restarted",
            f"{iso} CNTRLR   starting hardware watchdog...",
        ],
        "linky-01": [f"{iso} info teleinfo2mqtt: reconnecting to the mqtt broker..."]
        * 3
        + (
            []
            if dns_fixed
            else [
                f"{iso} warn teleinfo2mqtt: unable to publish frame to ohana-agent "
                "(connect ECONNREFUSED 127.0.1.1:8770)"
            ]
            * 150
        ),
        "ha-01": [
            f"{ha} ERROR (MainThread) [kasa.smart.smartdevice] "
            "Error querying 192.168.1.44 for modules"
        ]
        * 5
        + [
            f"{ha} WARNING (MainThread) [homeassistant.components.mqtt.client] "
            "Disconnected from MQTT server core-mosquitto:1883"
        ]
        * 3,
    }


def _daily_check(s, lines: dict[str, list[str]]) -> dict:
    s.service.request_log_health_check(now=s.clock(), max_bytes=65536, window_hours=24)
    claimed = s.service.next_worker_job(
        {"worker_id": WORKER, "supported_types": ["logs.health_check"]}
    ).job
    assert claimed is not None and claimed.type == "logs.health_check"

    def source_provider(job_id, worker_id, attempt, source):
        return {
            "source": source,
            "transport": "inline",
            "content": "\n".join(lines[source]),
            "truncated": False,
        }

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


def _active_log_sources(s) -> set[str]:
    return {
        incident.equipment_id
        for incident in s.incidents.list()
        if incident.capability_id == "logs.health"
        and incident.service_id in {"home-assistant", "system-journal"}
        and incident.state == "active"
    }


def run() -> dict:
    checks = []
    details = {}
    with environment() as s:
        s.service = AdministrationService(
            infrastructure_repository=InfrastructureConfigurationRepository(
                s.root / "infra.yaml"
            ),
            job_repository=s.jobs,
            incident_repository=s.incidents,
            expertise_service=s.expertise,
            log_sources=SOURCES,
        )
        s.jobs.register_worker(
            {
                "worker_id": WORKER,
                "platform": "Sandbox",
                "worker_version": "dev",
                "capabilities": ["logs.health_check", "ai.inference"],
            }
        )

        first = _daily_check(s, _lines(s.clock(), dns_fixed=False))
        by_source = {source["source"]: source for source in first["sources"]}
        active = _active_log_sources(s)
        checks += [
            (
                "jour 1 : INFO Ohana, déploiements et 20 délais sans incident INFRA-01",
                "infra-01" not in active and len(by_source["infra-01"]["findings"]) == 1,
            ),
            (
                "jour 1 : la sauvegarde NVM nocturne n'est pas une anomalie",
                "zwave-01" not in active and not by_source["zwave-01"]["findings"],
            ),
            (
                "jour 1 : 150 trames Linky refusées ouvrent un incident",
                "linky-01" in active,
            ),
            ("jour 1 : l'erreur Kasa ouvre un incident HA-01", "ha-01" in active),
        ]

        ha = next(
            incident
            for incident in s.incidents.list()
            if incident.equipment_id == "ha-01"
            and incident.capability_id == "logs.health"
            and incident.state == "active"
        )
        kasa = next(
            finding["signature"]
            for finding in ha.context["findings"]
            if "kasa" in finding["signature"]
        )
        checks.append(
            (
                "jour 1 : la déconnexion MQTT (3 avertissements) reste hors incident",
                [f["signature"] for f in ha.context["findings"]] == [kasa]
                and len(ha.context["background_findings"]) == 1,
            )
        )
        s.service.accept_log_signature({"source": "ha-01", "signature": kasa})
        checks.append(
            (
                "acceptation de Kasa : l'incident HA-01 est résolu aussitôt",
                s.incidents.get(ha.incident_id).state == "resolved",
            )
        )

        _daily_check(s, _lines(s.clock(), dns_fixed=True))
        checks += [
            (
                "jour 2 : DNS corrigé, l'incident LINKY-01 se résout",
                "linky-01" not in _active_log_sources(s),
            ),
            (
                "jour 2 : l'erreur Kasa acceptée ne rouvre rien",
                "ha-01" not in _active_log_sources(s),
            ),
            (
                "jour 2 : la signature reste listée comme acceptée",
                [
                    item["signature"]
                    for item in s.service.list_accepted_log_signatures()["signatures"]
                ]
                == [kasa],
            ),
        ]
        details["incidents actifs"] = ", ".join(sorted(_active_log_sources(s))) or "aucun"
    details["portée"] = (
        "Agent, Tsunade et analyseur Katsuyu locaux ; aucun accès production"
    )
    details["limites"] = "Lignes reconstituées ; sans transport HTTP ni IA"
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
