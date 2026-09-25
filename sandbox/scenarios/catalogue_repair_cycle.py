"""Catalogue repairs beyond dnsmasq: teleinfo2mqtt, Z-Wave JS and chrony.

Real Agent services, SQLite stores and executors: the add-on executor is the
Agent ``restart_addon`` talking to a simulated Supervisor, and the chrony
executor writes its restart request to a temporary file watched by nothing.
Nothing is restarted. Probe answers and Supervisor listings are simulated
with the production declarations and add-on slugs of Konoha.
"""

from __future__ import annotations

import tempfile
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from ohana_agent.api.service import AdministrationService
from ohana_agent.host.chrony import ChronyRestartRequester
from ohana_agent.infrastructure.repository import InfrastructureConfigurationRepository
from ohana_agent.observation import Observation, ObservationStatus
from ohana_agent.tsunade import configuration_inspection
from ohana_agent.tsunade.expertise import TsunadeExpertiseService
from ohana_agent.tsunade.incidents import TsunadeIncidentRepository
from ohana_agent.tsunade.investigations import InvestigationResult
from ohana_agent.tsunade.local_time import paris_now

INFRASTRUCTURE = """\
infrastructure: {id: konoha, name: Konoha}
nodes:
  - {id: infra-01, name: INFRA-01, endpoint: {type: ip, address: 192.168.1.10}}
  - {id: zwave-01, name: ZWAVE-01, endpoint: {type: ip, address: 192.168.1.30}}
  - {id: linky-01, name: LINKY-01, endpoint: {type: ip, address: 192.168.1.40}}
services:
  - {id: chrony, name: NTP, type: ntp, node: infra-01, implementation: NTP}
  - {id: zwave, name: Z-Wave JS, type: zwave, node: zwave-01,
     implementation: Z-Wave JS UI}
  - {id: tic-linky, name: Linky, type: teleinformation, node: linky-01,
     implementation: teleinfo2mqtt}
"""
SERVICES = {
    "chrony": ("infra-01", "ntp.query"),
    "zwave": ("zwave-01", "zwave.status"),
    "tic-linky": ("linky-01", "teleinformation.freshness"),
}
TELEINFO = "6fc079ce_teleinfo2mqtt_ohana"
ZWAVE = "a0d7b954_zwavejs2mqtt"


@dataclass
class Konoha:
    """Simulated probe answers and Supervisor of the failing node."""

    results: dict[str, dict] = field(default_factory=dict)
    addons: list[dict] | None = None
    supervisor_accepts: bool = True
    snapshots: list[str] = field(default_factory=list)
    supervisor_calls: list[tuple[str, str, str]] = field(default_factory=list)

    def execute(self, payload):
        now = paris_now()
        return InvestigationResult(
            investigation_id=uuid4(),
            operation=payload["operation"],
            status="OK",
            started_at=now,
            finished_at=now,
            duration_seconds=0,
            result=self.results.get(payload["operation"], {"success": True}),
        )

    def read_only_snapshot(self, node_id: str) -> dict:
        self.snapshots.append(node_id)
        if self.addons is None:
            raise ConnectionError("Supervisor injoignable")
        return {"configuration_inspection": {"remote": {"addons": self.addons}}}

    def supervisor_api(self):
        @asynccontextmanager
        async def api(_config, node_id, *, timeout_seconds=8):
            async def call(endpoint, method):
                self.supervisor_calls.append((node_id, endpoint, method))
                if self.supervisor_accepts:
                    return {"success": True}
                return {"success": False, "error": {"message": "add-on occupé"}}

            yield call

        return api


@dataclass
class Lab:
    konoha: Konoha
    request: Path
    incidents: TsunadeIncidentRepository
    service: AdministrationService
    expertise: TsunadeExpertiseService

    def observe(self, service_id: str, healthy: bool):
        node, capability = SERVICES[service_id]
        status = ObservationStatus.HEALTHY if healthy else ObservationStatus.UNHEALTHY
        return self.incidents.process(
            Observation(
                node=node,
                service=service_id,
                capability=capability,
                status=status,
                success=healthy,
                message=f"{service_id} is {status.value}",
                source=capability,
                id=uuid4(),
                timestamp=paris_now(),
                metadata={"device_id": node, "mode": "direct_http"},
            )
        )

    def diagnose(self, service_id: str):
        incident = self.observe(service_id, healthy=False)
        outcome = self.expertise.diagnose(incident.incident_id)
        return outcome, self.incidents.get(incident.incident_id)

    def authorize(self, incident):
        [repair] = incident.repairs
        return self.service.authorize_incident_repair(
            str(incident.incident_id),
            {"repair_id": str(repair.repair_id), "source": "vision"},
        )

    def verify(self, service_id: str, incident):
        self.observe(service_id, healthy=True)
        return self.incidents.get(incident.incident_id)


@contextmanager
def _lab(konoha: Konoha, *, helper_installed: bool = True):
    original = configuration_inspection.supervisor_api
    configuration_inspection.supervisor_api = konoha.supervisor_api()
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-catalogue-") as temporary:
        root = Path(temporary)
        (root / "infrastructure.yaml").write_text(INFRASTRUCTURE, encoding="utf-8")
        path_unit = root / "ohana-chrony-restart.path"
        if helper_installed:
            path_unit.write_text("[Path]\n", encoding="utf-8")
        request = root / "run" / "chrony-restart.request"
        chrony = ChronyRestartRequester(request_path=request, path_unit=path_unit)

        def restart_addon(incident, target):
            configuration_inspection.restart_addon(object(), incident.node_id, target)

        incidents = TsunadeIncidentRepository(root / "incidents.db")
        service = AdministrationService(
            infrastructure_repository=InfrastructureConfigurationRepository(
                root / "infrastructure.yaml"
            ),
            incident_repository=incidents,
            repair_executors={
                "teleinfo2mqtt.restart": restart_addon,
                "zwave_js.restart": restart_addon,
                "chrony.restart": lambda _incident, _target: chrony.request_restart(),
            },
            agent_node_id="infra-01",
        )
        expertise = TsunadeExpertiseService(incidents=incidents, investigations=konoha)
        expertise.set_repair_proposer(
            lambda incident_id: service.propose_incident_repair(
                str(incident_id), {}, automatic=True
            )
        )
        try:
            yield Lab(konoha, request, incidents, service, expertise)
        finally:
            incidents.close()
            configuration_inspection.supervisor_api = original


def _teleinformation(checks, details):
    konoha = Konoha(addons=[{"addon": TELEINFO, "state": "stopped"}])
    with _lab(konoha) as lab:
        outcome, incident = lab.diagnose("tic-linky")
        [repair] = incident.repairs or [None]
        checks += [
            (
                "teleinfo2mqtt : arrêt confirmé par le Supervisor de LINKY-01, "
                "sans IA",
                outcome.decision == "action_required"
                and incident.latest_decision["epistemic_status"]
                == "confirmed_by_supervisor"
                and konoha.snapshots == ["linky-01"],
            ),
            (
                "teleinfo2mqtt : Tsunade propose seul le redémarrage de l'add-on "
                "listé, à risque faible",
                repair is not None
                and (repair.status, repair.target, repair.risk)
                == ("proposed", TELEINFO, "low")
                and "teleinfo2mqtt" in (repair.action or ""),
            ),
            (
                "teleinfo2mqtt : aucune action sans autorisation",
                not konoha.supervisor_calls,
            ),
        ]
        verifying = lab.authorize(incident)
        final = lab.verify("tic-linky", incident)
        checks += [
            (
                "teleinfo2mqtt : autorisation Vision → redémarrage demandé au "
                "Supervisor de LINKY-01",
                verifying.status == "verifying"
                and konoha.supervisor_calls
                == [("linky-01", f"/addons/{TELEINFO}/restart", "post")],
            ),
            (
                "teleinfo2mqtt : trames revenues, réparation vérifiée par "
                "Shikamaru et mémorisable",
                final.state == "resolved"
                and final.repairs[0].status == "succeeded"
                and final.experience_candidate is not None,
            ),
        ]

    konoha = Konoha(addons=[{"addon": TELEINFO, "state": "started"}])
    with _lab(konoha) as lab:
        _outcome, incident = lab.diagnose("tic-linky")
        checks.append(
            (
                "teleinfo2mqtt démarré : trames absentes mais aucune réparation",
                not incident.repairs and not konoha.supervisor_calls,
            )
        )
    details["teleinfo2mqtt"] = f"{TELEINFO} redémarré et vérifié"


def _zwave(checks, details):
    konoha = Konoha(
        results={"zwave.status": {"success": False, "message": "Connection refused"}},
        addons=[{"addon": ZWAVE, "state": "started"}],
    )
    with _lab(konoha) as lab:
        outcome, incident = lab.diagnose("zwave")
        [repair] = incident.repairs or [None]
        checks += [
            (
                "Z-Wave JS : pilote en échec confirmé par zwave.status, add-on "
                "inspecté sur ZWAVE-01",
                incident.latest_decision["epistemic_status"] == "confirmed_by_probe"
                and konoha.snapshots == ["zwave-01"]
                and any(ZWAVE in fact for fact in outcome.facts),
            ),
            (
                "Z-Wave JS : redémarrage de l'add-on listé proposé à risque moyen",
                repair is not None
                and (repair.status, repair.target, repair.risk)
                == ("proposed", ZWAVE, "medium"),
            ),
        ]
        lab.authorize(incident)
        final = lab.verify("zwave", incident)
        checks.append(
            (
                "Z-Wave JS : Supervisor de ZWAVE-01 sollicité, pilote revenu, "
                "réparation vérifiée",
                konoha.supervisor_calls
                == [("zwave-01", f"/addons/{ZWAVE}/restart", "post")]
                and final.repairs[0].status == "succeeded",
            )
        )

    konoha = Konoha(
        results={"zwave.status": {"success": False}},
        addons=[{"addon": ZWAVE, "state": "started"}],
        supervisor_accepts=False,
    )
    with _lab(konoha) as lab:
        _outcome, incident = lab.diagnose("zwave")
        failed = lab.authorize(incident)
        checks.append(
            (
                "Z-Wave JS : refus du Supervisor → échec explicite, jamais "
                "reproposé",
                failed.status == "failed"
                and "add-on occupé" in (failed.result or "")
                and lab.service.propose_incident_repair(
                    str(incident.incident_id), {}, automatic=True
                )
                is None,
            )
        )

    konoha = Konoha(results={"zwave.status": {"success": False}}, addons=None)
    with _lab(konoha) as lab:
        _outcome, incident = lab.diagnose("zwave")
        checks.append(
            (
                "Z-Wave JS : Supervisor injoignable → aucune cible, aucune "
                "proposition",
                incident.latest_decision["epistemic_status"] == "confirmed_by_probe"
                and not incident.repairs,
            )
        )
    details["Z-Wave JS"] = f"{ZWAVE} redémarré, refus et Supervisor absent"


def _chrony(checks, details):
    stopped = {
        "ntp.status": {"success": False, "error": "timed out"},
        "chrony.status": {"success": False, "service_active": False},
    }
    konoha = Konoha(results=stopped)
    with _lab(konoha) as lab:
        _outcome, incident = lab.diagnose("chrony")
        [repair] = incident.repairs or [None]
        checks.append(
            (
                "chrony : arrêt local confirmé par chrony.status, redémarrage "
                "proposé sans Supervisor",
                repair is not None
                and (repair.status, repair.target) == ("proposed", "chrony.service")
                and not konoha.snapshots
                and not lab.request.exists(),
            )
        )
        verifying = lab.authorize(incident)
        final = lab.verify("chrony", incident)
        checks.append(
            (
                "chrony : autorisation → demande écrite pour l'assistant "
                "privilégié, NTP revenu, réparation vérifiée",
                verifying.status == "verifying"
                and '"schema_version":1' in lab.request.read_text(encoding="utf-8")
                and final.repairs[0].status == "succeeded",
            )
        )

    konoha = Konoha(
        results={
            "ntp.status": {"success": False},
            "chrony.status": {"success": True, "service_active": True},
        }
    )
    with _lab(konoha) as lab:
        _outcome, incident = lab.diagnose("chrony")
        checks.append(
            (
                "chrony actif, sources amont en échec : aucune réparation",
                not incident.repairs,
            )
        )

    konoha = Konoha(results=stopped)
    with _lab(konoha, helper_installed=False) as lab:
        _outcome, incident = lab.diagnose("chrony")
        failed = lab.authorize(incident)
        checks.append(
            (
                "chrony sans assistant installé : échec explicite, aucune "
                "demande écrite",
                failed.status == "failed"
                and "n’est pas installé" in (failed.result or "")
                and not lab.request.exists(),
            )
        )
    details["chrony"] = "demande écrite vers un fichier temporaire"


def run() -> dict:
    checks: list[tuple[str, bool]] = []
    details: dict[str, str] = {}
    for part in (_teleinformation, _zwave, _chrony):
        part(checks, details)
    details["portée"] = (
        "Services Agent et SQLite réels ; restart_addon réel vers un Supervisor "
        "simulé ; demande chrony réelle vers un fichier temporaire"
    )
    details["limites"] = (
        "Aucun add-on ni chrony redémarré ; sondes et listes d'add-ons simulées"
    )
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
