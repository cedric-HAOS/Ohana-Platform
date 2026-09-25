"""Phase 2 supervised repair cycle with the real Agent dnsmasq executor.

The dnsmasq restart request is written to a temporary file instead of the
production helper directory: nothing is restarted. Probe answers are
simulated; proposal, authorization, execution, verification and learning run
through the real Agent services and SQLite stores.
"""

from __future__ import annotations

import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from ohana_agent.api.service import AdministrationService
from ohana_agent.host.dhcp import DnsmasqDHCPRepository
from ohana_agent.infrastructure.repository import InfrastructureConfigurationRepository
from ohana_agent.observation import Observation, ObservationStatus
from ohana_agent.tsunade import incident_repairs
from ohana_agent.tsunade.expertise import TsunadeExpertiseService
from ohana_agent.tsunade.incidents import TsunadeIncidentRepository
from ohana_agent.tsunade.investigations import InvestigationResult
from ohana_agent.tsunade.local_time import paris_now

INFRASTRUCTURE = """\
infrastructure: {id: konoha, name: Konoha}
nodes:
  - {id: infra-01, name: INFRA-01, endpoint: {type: ip, address: 192.168.1.10}}
services:
  - {id: dhcp, name: DHCP, type: dhcp, node: infra-01, implementation: dnsmasq}
"""


class DnsmasqStopped:
    """dhcp.status answers as the Agent plugin does when dnsmasq is inactive."""

    def execute(self, payload):
        now = paris_now()
        return InvestigationResult(
            investigation_id=uuid4(),
            operation=payload["operation"],
            status="OK",
            started_at=now,
            finished_at=now,
            duration_seconds=0,
            result={"success": False, "metadata": {"service_active": False}},
        )


@dataclass
class Lab:
    root: Path
    reload_request: Path
    incidents: TsunadeIncidentRepository
    service: AdministrationService
    expertise: TsunadeExpertiseService

    def observe(self, status: ObservationStatus):
        return self.incidents.process(
            Observation(
                node="infra-01",
                service="dhcp",
                capability="dhcp.status",
                status=status,
                success=status is ObservationStatus.HEALTHY,
                message=f"dnsmasq is {status.value}",
                source="dhcp.status",
                id=uuid4(),
                timestamp=paris_now(),
                metadata={"device_id": "infra-01"},
            )
        )

    def incident(self, incident_id):
        return self.incidents.get(incident_id)


def _build(root: Path, *, helper_installed: bool) -> Lab:
    reload_request = root / "run" / "dhcp-reload.request"
    infrastructure = root / "infrastructure.yaml"
    if not infrastructure.exists():
        infrastructure.write_text(INFRASTRUCTURE, encoding="utf-8")
    incidents = TsunadeIncidentRepository(root / "incidents.db")
    service = AdministrationService(
        infrastructure_repository=InfrastructureConfigurationRepository(infrastructure),
        incident_repository=incidents,
        dhcp_repository=DnsmasqDHCPRepository(
            main_config_path=root / "dnsmasq.conf",
            reservation_paths={},
            leases_path=root / "leases",
            reload_request_path=reload_request if helper_installed else None,
        ),
    )
    expertise = TsunadeExpertiseService(
        incidents=incidents, investigations=DnsmasqStopped()
    )
    expertise.set_repair_proposer(
        lambda incident_id: service.propose_incident_repair(
            str(incident_id), {}, automatic=True
        )
    )
    return Lab(root, reload_request, incidents, service, expertise)


@contextmanager
def _lab(*, helper_installed: bool = True):
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-repair-") as temporary:
        lab = _build(Path(temporary), helper_installed=helper_installed)
        try:
            yield lab
        finally:
            lab.incidents.close()


def _restart(lab: Lab) -> Lab:
    lab.incidents.close()
    return _build(lab.root, helper_installed=True)


def _decision(repair_id, source="vision"):
    return {"repair_id": str(repair_id), "source": source}


def _raises(call) -> bool:
    try:
        call()
    except (LookupError, ValueError):
        return True
    return False


def _reference(checks, details):
    with _lab() as lab:
        incident = lab.observe(ObservationStatus.UNHEALTHY)
        outcome = lab.expertise.diagnose(incident.incident_id)
        repairs = lab.incident(incident.incident_id).repairs
        checks += [
            (
                "référence : dnsmasq arrêté confirmé par sonde, sans IA",
                outcome.status == "DETERMINISTIC"
                and lab.incident(incident.incident_id).latest_decision[
                    "epistemic_status"
                ]
                == "confirmed_by_probe",
            ),
            (
                "référence : Tsunade propose seul le redémarrage de dnsmasq",
                [(r.status, r.target) for r in repairs]
                == [("proposed", "dnsmasq.service")],
            ),
            (
                "référence : une demande d'autorisation attend l'utilisateur",
                len(lab.service.read_companion_requests().requests) == 1,
            ),
            (
                "référence : rien n'est exécuté avant autorisation",
                not lab.reload_request.exists(),
            ),
            (
                "référence : une proposition inconnue ne peut pas être autorisée",
                _raises(
                    lambda: lab.service.authorize_incident_repair(
                        str(incident.incident_id), _decision(uuid4())
                    )
                )
                and not lab.reload_request.exists(),
            ),
        ]
        repair = repairs[0]
        deferred = lab.service.defer_incident_repair(
            str(incident.incident_id), _decision(repair.repair_id)
        )
        lab = _restart(lab)
        kept = lab.incident(incident.incident_id).repairs[0]
        checks += [
            (
                "référence : le report depuis Vision garde la proposition en attente",
                deferred.status == "proposed" and deferred.deferred_until is not None,
            ),
            (
                "référence : le report survit à la reprise SQLite",
                kept.status == "proposed"
                and kept.deferred_until == deferred.deferred_until,
            ),
            (
                "référence : rien n'est exécuté pendant le report",
                not lab.reload_request.exists(),
            ),
        ]
        verifying = lab.service.authorize_incident_repair(
            str(incident.incident_id), _decision(repair.repair_id)
        )
        executed_once = lab.reload_request.exists()
        lab = _restart(lab)
        checks += [
            (
                "référence : l'autorisation Vision exécute la demande dnsmasq une fois",
                executed_once and verifying.status == "verifying",
            ),
            (
                "référence : la vérification en attente survit à la reprise",
                lab.incident(incident.incident_id).repairs[0].status == "verifying",
            ),
            (
                "référence : l'échéance de vérification est enregistrée",
                verifying.verification_deadline is not None
                and verifying.verification_deadline > verifying.executed_at,
            ),
        ]
        lab.observe(ObservationStatus.HEALTHY)
        verified = lab.incident(incident.incident_id)
        checks += [
            (
                "référence : Shikamaru confirme, la réparation réussit",
                verified.state == "resolved"
                and verified.repairs[0].status == "succeeded",
            ),
            (
                "référence : la réparation peut devenir une expérience connue",
                verified.experience_candidate is not None,
            ),
        ]
        experience = lab.service.confirm_incident_experience(
            str(incident.incident_id),
            {"confirm": True, "source": "vision", "confirmed_by": "sandbox"},
        )
        checks.append(
            (
                "référence : l'expérience est apprise après confirmation",
                experience.success_count == 1,
            )
        )
        details["référence"] = "proposée, reportée, autorisée, vérifiée, apprise"
        lab.incidents.close()


def _refusal(checks, details):
    with _lab() as lab:
        incident = lab.observe(ObservationStatus.UNHEALTHY)
        lab.expertise.diagnose(incident.incident_id)
        [request] = lab.service.read_companion_requests().requests
        lab.service.respond_companion_request(
            str(request.request_id), "sandbox-iphone", {"choice": "REFUSE"}
        )
        repair = lab.incident(incident.incident_id).repairs[0]
        lab.expertise.diagnose(incident.incident_id)
        checks += [
            (
                "refus : le refus depuis Shizune est enregistré",
                repair.status == "refused",
            ),
            (
                "refus : une réparation refusée ne peut plus être autorisée",
                _raises(
                    lambda: lab.service.authorize_incident_repair(
                        str(incident.incident_id), _decision(repair.repair_id)
                    )
                ),
            ),
            (
                "refus : un nouveau diagnostic ne repropose rien",
                len(lab.incident(incident.incident_id).repairs) == 1,
            ),
            ("refus : aucune exécution", not lab.reload_request.exists()),
        ]
        details["refus"] = "définitif, sans exécution ni nouvelle proposition"


def _failure(checks, details):
    with _lab(helper_installed=False) as lab:
        incident = lab.observe(ObservationStatus.UNHEALTHY)
        lab.expertise.diagnose(incident.incident_id)
        repair = lab.incident(incident.incident_id).repairs[0]
        failed = lab.service.authorize_incident_repair(
            str(incident.incident_id), _decision(repair.repair_id)
        )
        lab.expertise.diagnose(incident.incident_id)
        after = lab.incident(incident.incident_id)
        checks += [
            (
                "échec : l'échec d'exécution est explicite",
                failed.status == "failed"
                and "n’est pas installé" in (failed.result or ""),
            ),
            ("échec : l'incident reste actif", after.state == "active"),
            (
                "échec : la réparation n'est pas reproposée seule",
                len(after.repairs) == 1,
            ),
        ]
        details["échec"] = "failed, incident actif, pas de répétition"


def _unverified(checks, details):
    with _lab() as lab:
        incident = lab.observe(ObservationStatus.UNHEALTHY)
        lab.expertise.diagnose(incident.incident_id)
        repair = lab.incident(incident.incident_id).repairs[0]
        # Production waits at least 5 minutes; the lab shortens only this delay,
        # which is fixed when the repair runs.
        original = (
            incident_repairs.REPAIR_VERIFICATION_SECONDS,
            incident_repairs.REPAIR_VERIFICATION_MIN_SECONDS,
        )
        incident_repairs.REPAIR_VERIFICATION_SECONDS = 1
        incident_repairs.REPAIR_VERIFICATION_MIN_SECONDS = 1
        try:
            lab.service.authorize_incident_repair(
                str(incident.incident_id), _decision(repair.repair_id)
            )
        finally:
            (
                incident_repairs.REPAIR_VERIFICATION_SECONDS,
                incident_repairs.REPAIR_VERIFICATION_MIN_SECONDS,
            ) = original
        time.sleep(1.2)
        unverified = lab.incident(incident.incident_id).repairs[0]
        lab.observe(ObservationStatus.HEALTHY)
        late = lab.incident(incident.incident_id)
        checks += [
            (
                "non vérifiée : sans confirmation Shikamaru, la réparation est unverified",
                unverified.status == "unverified",
            ),
            (
                "non vérifiée : une observation tardive ne la réécrit pas en succès",
                late.state == "resolved" and late.repairs[0].status == "unverified",
            ),
        ]
        details["non vérifiée"] = "unverified après le délai, jamais réécrite"


def _expired(checks, details):
    with _lab() as lab:
        incident = lab.observe(ObservationStatus.UNHEALTHY)
        lab.expertise.diagnose(incident.incident_id)
        repair = lab.incident(incident.incident_id).repairs[0]
        lab.observe(ObservationStatus.HEALTHY)
        checks += [
            (
                "expiration : l'incident résolu fait expirer la proposition",
                lab.incident(incident.incident_id).repairs[0].status == "expired",
            ),
            (
                "expiration : une proposition expirée ne peut plus être autorisée",
                _raises(
                    lambda: lab.service.authorize_incident_repair(
                        str(incident.incident_id), _decision(repair.repair_id)
                    )
                )
                and not lab.reload_request.exists(),
            ),
        ]
        details["expiration"] = "expired, aucune exécution"


def run() -> dict:
    checks: list[tuple[str, bool]] = []
    details: dict[str, str] = {}
    for part in (_reference, _refusal, _failure, _unverified, _expired):
        part(checks, details)
    details["portée"] = (
        "Services Agent et SQLite réels ; exécuteur dnsmasq réel vers un fichier "
        "temporaire ; sondes simulées"
    )
    details["limites"] = (
        "Aucun redémarrage réel de dnsmasq ; délai de vérification réduit"
    )
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
