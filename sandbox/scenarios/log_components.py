"""HA-01 noise read by component, as it looked on 29 September.

Production: the HA-01 review listed 38 anomalies of a dozen integrations (Tapo,
Kasa, Shelly, Roomba, ESPHome, templates...). Vision showed eight of them, by
signature, and the user could not find "Tapo" or "Kasa" in it. Python's chained
tracebacks (blank lines between the parts) also made five orphan findings, and
each Shelly device made its own signature.

The real Katsuyu analyser reads the lines below; the Agent names each anomaly's
component, accepts a whole component (never its critical lines) and does not
reopen when the component's text changes the next day.
"""

from __future__ import annotations

from datetime import timedelta

from ohana_agent.api.service import AdministrationService
from ohana_agent.infrastructure.repository import InfrastructureConfigurationRepository

from scenarios._support import environment
from scenarios.log_noise_triage import SOURCES, WORKER, _daily_check, _lines


def _ha_lines(now, *, tapo_tail: str, critical: bool) -> list[str]:
    stamp = (now - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    tapo = [
        f"{stamp} ERROR (MainThread) [custom_components.tapo_control] "
        f"Unable to connect to Tapo: {tapo_tail}",
        "Traceback (most recent call last):",
        '  File "/usr/local/lib/python3.13/site-packages/urllib3/connection.py", '
        "line 174, in _new_conn",
        "urllib3.exceptions.ConnectTimeoutError: timed out",
        "",
        "During handling of the above exception, another exception occurred:",
        "",
        "Traceback (most recent call last):",
        "    raise exception",
        "requests.exceptions.ConnectTimeout: HTTPSConnectionPool",
        "",
        "The above exception was the direct cause of the following exception:",
    ]
    lines = tapo * 4
    lines += [
        f"{stamp} ERROR (MainThread) [kasa.smart.smartdevice] "
        "Error querying 192.168.1.44 for modules"
    ] * 5
    lines += [
        f"{stamp} ERROR (MainThread) [homeassistant.components.shelly] "
        f"Error fetching shellyproem50-{device} data: Timeout"
        for device in ("441d64760b64", "08f9e0e7dc2c", "34987aa84b8c")
    ]
    if critical:
        lines.append(
            f"{stamp} CRITICAL (MainThread) [custom_components.tapo_control] "
            "Camera firmware rejected the session"
        )
    return lines


def _findings(s, source: str, ignored: set) -> list[dict]:
    incident = next(
        (
            item
            for item in s.incidents.list()
            if item.equipment_id == source
            and item.capability_id == "logs.health"
            and item.state == "active"
            and item.incident_id not in ignored
        ),
        None,
    )
    return incident.context["findings"] if incident else []


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

        # The Sandbox fixture already holds an unrelated HA-01 incident.
        ignored = {item.incident_id for item in s.incidents.list()}
        base = _lines(s.clock(), linky=[])
        first = _daily_check(
            s,
            {
                **base,
                "ha-01": _ha_lines(s.clock(), tapo_tail="timeout 1", critical=True),
            },
        )
        ha = next(source for source in first["sources"] if source["source"] == "ha-01")
        signatures = [finding["signature"] for finding in ha["findings"]]
        orphans = [
            signature
            for signature in signatures
            if signature.startswith(
                ("traceback", "the above exception", "during handling", "raise ")
            )
            or "exceptions." in signature.split("]")[0]
        ]
        shelly = [item for item in signatures if "shelly" in item]
        checks += [
            (
                "chaînes de traceback : aucune ligne orpheline en anomalie",
                not orphans,
            ),
            (
                "trois appareils Shelly du même modèle : une seule signature",
                len(shelly) == 1
                and next(
                    item["occurrences"]
                    for item in ha["findings"]
                    if item["signature"] == shelly[0]
                )
                == 3,
            ),
        ]

        overview = s.service.list_incidents()["log_components"]
        components = {
            item["label"]: item
            for source in overview
            if source["source"] == "ha-01"
            for item in source["components"]
        }
        checks.append(
            (
                "le contrôle nomme Tapo, Kasa et Shelly, pas leurs signatures",
                {"Tapo", "Kasa", "Shelly"} <= set(components)
                and components["Tapo"]["severity"] == "critical",
            )
        )

        s.service.accept_log_component(
            {"source": "ha-01", "component": "tapo_control", "label": "Tapo"}
        )
        s.service.accept_log_component(
            {"source": "ha-01", "component": "kasa", "label": "Kasa"}
        )
        s.service.accept_log_component(
            {"source": "ha-01", "component": "shelly", "label": "Shelly"}
        )
        remaining = _findings(s, "ha-01", ignored)
        checks.append(
            (
                "composants acceptés : seule la ligne critique de Tapo compte encore",
                [item["severity"] for item in remaining] == ["critical"]
                and remaining[0]["component"] == "tapo_control",
            )
        )

        s.clock.advance(days=1)
        create_job = s.jobs.create
        s.expertise.ai_dispatcher = lambda payload: create_job(
            {**payload, "created_at": s.clock().isoformat()}
        )
        _daily_check(
            s,
            {
                **_lines(s.clock(), linky=[]),
                "ha-01": _ha_lines(
                    s.clock(), tapo_tail="connection refused 2", critical=False
                ),
            },
        )
        checks.append(
            (
                "le lendemain, un nouveau texte d'erreur Tapo ne rouvre aucun incident",
                not _findings(s, "ha-01", ignored),
            )
        )

        accepted = s.service.list_accepted_log_signatures()["components"]
        s.service.revoke_log_component({"source": "ha-01", "component": "kasa"})
        checks.append(
            (
                "les composants acceptés restent listés puis se comptent à nouveau",
                {item["component"] for item in accepted}
                == {"tapo_control", "kasa", "shelly"}
                and len(s.service.list_accepted_log_signatures()["components"]) == 2,
            )
        )
        details["composants HA-01"] = ", ".join(sorted(components))
    details["portée"] = (
        "Agent, Tsunade et analyseur Katsuyu locaux ; aucun accès production"
    )
    details["limites"] = "Lignes reconstituées ; sans transport HTTP ni IA"
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
