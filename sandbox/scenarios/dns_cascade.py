"""A dnsmasq outage seen first as name lookup failures elsewhere.

Real Tsunade observation handler, SQLite incidents, expertise and
administration service. Probe answers are simulated with Konoha's messages of
26 September (dnsmasq stopped at 17:25:42). The DHCP observation that the
Agent requests on the first lookup failure is simulated by processing the
dnsmasq observation at once, as the scheduler would at its next tick.
"""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from ohana_agent.api.service import AdministrationService
from ohana_agent.infrastructure.repository import InfrastructureConfigurationRepository
from ohana_agent.observation import Observation, ObservationStatus
from ohana_agent.runtime.administration_bootstrap import TsunadeObservationHandler
from ohana_agent.tsunade.expertise import TsunadeExpertiseService
from ohana_agent.tsunade.incidents import TsunadeIncidentRepository
from ohana_agent.tsunade.investigations import InvestigationResult
from ohana_agent.tsunade.local_time import paris_now

INFRASTRUCTURE = """\
infrastructure: {id: konoha, name: Konoha}
nodes:
  - {id: infra-01, name: INFRA-01, endpoint: {type: ip, address: 192.168.1.10}}
  - {id: zwave-01, name: ZWAVE-01, endpoint: {type: ip, address: 192.168.1.11}}
services:
  - {id: dhcp, name: DHCP, type: dhcp, node: infra-01, implementation: dnsmasq}
  - {id: zwave, name: Z-Wave JS, type: zwave, node: zwave-01,
     implementation: Z-Wave JS UI}
"""
ZWAVE_LOOKUP = (
    "Z-Wave JS Server connection failed: Cannot connect to host "
    "zwave-01.ohana.lan:3000 ssl:default [No address associated with hostname]"
)


class Konoha:
    """Probe answers while dnsmasq is stopped."""

    def __init__(self, infrastructure: InfrastructureConfigurationRepository) -> None:
        self.infrastructure_reader = infrastructure.read
        self.snapshots: list[str] = []

    def execute(self, payload):
        now = paris_now()
        results = {
            "dhcp.status": {"success": False, "metadata": {"service_active": False}},
            "zwave.status": {"success": False, "message": ZWAVE_LOOKUP},
        }
        return InvestigationResult(
            investigation_id=uuid4(),
            operation=payload["operation"],
            status="OK",
            started_at=now,
            finished_at=now,
            duration_seconds=0,
            result=results.get(payload["operation"], {"success": True}),
        )

    def read_only_snapshot(self, node_id: str) -> dict:
        self.snapshots.append(node_id)
        return {"configuration_inspection": {"remote": {"addons": []}}}


def _observation(node, service, capability, message) -> Observation:
    return Observation(
        node=node,
        service=service,
        capability=capability,
        status=ObservationStatus.UNHEALTHY,
        success=False,
        message=message,
        source=capability,
        id=uuid4(),
        timestamp=paris_now(),
        metadata={"device_id": node},
    )


def _wait(predicate, timeout: float = 20.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.1)
    return predicate()


def run() -> dict:
    checks: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-dns-cascade-") as tmp:
        root = Path(tmp)
        (root / "infrastructure.yaml").write_text(INFRASTRUCTURE, encoding="utf-8")
        infrastructure = InfrastructureConfigurationRepository(
            root / "infrastructure.yaml"
        )
        incidents = TsunadeIncidentRepository(root / "incidents.db")
        restarted: list[str] = []
        service = AdministrationService(
            infrastructure_repository=infrastructure,
            incident_repository=incidents,
            repair_executors={
                "dnsmasq.restart": lambda _incident, target: restarted.append(target),
                "zwave_js.restart": lambda _incident, target: restarted.append(target),
            },
            agent_node_id="infra-01",
        )
        dispatched: list[dict] = []
        expertise = TsunadeExpertiseService(
            incidents=incidents,
            investigations=Konoha(infrastructure),  # type: ignore[arg-type]
            ai_dispatcher=lambda payload: dispatched.append(payload)
            or SimpleNamespace(job_id=uuid4()),
        )
        expertise.set_repair_proposer(
            lambda incident_id: service.propose_incident_repair(
                str(incident_id), {}, automatic=True
            )
        )
        requested: list[str] = []
        handler: TsunadeObservationHandler

        def dhcp_observed_now() -> None:
            # The DHCP task runs at the next scheduler tick instead of 30 min.
            requested.append("dhcp")
            handler(
                SimpleNamespace(
                    observation=_observation(
                        "infra-01",
                        "dhcp",
                        "dhcp.status",
                        "DHCP service is not active: inactive",
                    )
                )
            )

        try:
            handler = TsunadeObservationHandler(
                incidents=incidents,
                expertise=expertise,
                administration=service,
                logs_config=SimpleNamespace(enabled=False, sources=()),  # type: ignore[arg-type]
                notifications=None,
                on_name_lookup_failure=dhcp_observed_now,
            )
            handler(
                SimpleNamespace(
                    observation=_observation(
                        "zwave-01", "zwave", "zwave.status", ZWAVE_LOOKUP
                    )
                )
            )
            active = {item.service_id: item for item in incidents.list()}
            checks.append(
                (
                    "échec de résolution Z-Wave → observation DHCP immédiate, "
                    "incident dnsmasq ouvert sans attendre le cycle de 30 min",
                    requested == ["dhcp"] and {"zwave", "dhcp"} <= set(active),
                )
            )
            zwave_id = active["zwave"].incident_id if "zwave" in active else None
            dhcp_id = active["dhcp"].incident_id if "dhcp" in active else None

            def decided(incident_id) -> bool:
                return incident_id is not None and bool(
                    incidents.get(incident_id).latest_decision
                )

            _wait(lambda: decided(zwave_id) and decided(dhcp_id))
            zwave = incidents.get(zwave_id) if zwave_id else None
            dhcp = incidents.get(dhcp_id) if dhcp_id else None
            decision = (zwave.latest_decision or {}) if zwave else {}
            checks += [
                (
                    "symptôme Z-Wave rattaché à l'incident dnsmasq, décision watch",
                    decision.get("epistemic_status") == "correlated_with_upstream"
                    and decision.get("upstream_incident_id") == str(dhcp_id)
                    and decision.get("decision") == "watch",
                ),
                (
                    "aucune réparation Z-Wave JS proposée, aucune expertise IA",
                    zwave is not None and not zwave.repairs and not dispatched,
                ),
                (
                    "redémarrage supervisé de dnsmasq proposé sur l'incident amont",
                    dhcp is not None
                    and [(item.status, item.target) for item in dhcp.repairs]
                    == [("proposed", "dnsmasq.service")],
                ),
                ("rien n'est exécuté sans autorisation", restarted == []),
            ]
        finally:
            incidents.close()
    return {
        "passed": all(passed for _, passed in checks),
        "checks": checks,
        "details": {"expertises IA": len(dispatched)},
    }
