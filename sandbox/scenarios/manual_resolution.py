"""Phase 3, lot 3: a manual resolution declared by the user.

Through the real Agent services and SQLite stores: the user declares what
they did by hand, Shikamaru must see the capability recover afterwards, and
Tsunade asks before keeping it. The kept lead is a note: it must never turn
into an executable repair, even when it reads like a command.
"""

from __future__ import annotations

import json

from ohana_agent.observation import ObservationStatus
from ohana_agent.tsunade import incident_manual

from scenarios.supervised_repair_cycle import _build, _decision, _lab, _restart

COMMAND = "sudo systemctl restart dnsmasq.service"


def _declare(lab, incident, description=COMMAND):
    return lab.service.declare_manual_resolution(
        str(incident.incident_id),
        {"description": description, "source": "vision", "declared_by": "sandbox"},
    )


def run() -> dict:
    checks = []
    details = {}
    with _lab() as lab:
        try:
            incident = lab.observe(ObservationStatus.UNHEALTHY)
            action = _declare(lab, incident)
            checks.append(
                (
                    "déclaration : action manuelle en attente de Shikamaru",
                    action.status == "verifying" and not lab.reload_request.exists(),
                )
            )
            lab.observe(ObservationStatus.HEALTHY)
            resolved = lab.incident(incident.incident_id)
            candidate = resolved.experience_candidate
            checks += [
                (
                    "Shikamaru confirme le retour à l'état sain après l'action",
                    resolved.manual_actions[0].status == "confirmed",
                ),
                (
                    "Tsunade demande avant de capitaliser, sans rien apprendre seule",
                    candidate is not None
                    and candidate.kind == "manual"
                    and "semble avoir participé" in candidate.prompt
                    and lab.service.list_experiences()["experiences"] == [],
                ),
                (
                    "la proximité temporelle n'est pas présentée comme une preuve",
                    "ne prouve pas à elle seule" in (candidate.caution or ""),
                ),
            ]
            lab.service.confirm_incident_experience(
                str(incident.incident_id),
                {"confirm": True, "source": "vision", "confirmed_by": "sandbox"},
            )
            [lead] = lab.service.list_experiences()["experiences"]
            checks.append(
                (
                    "la piste manuelle est conservée comme note",
                    lead["action"] == {"kind": "manual", "description": COMMAND},
                )
            )

            # A later dnsmasq failure: the lead is shown, never executed.
            lab = _restart(lab)
            again = lab.observe(ObservationStatus.UNHEALTHY)
            lab.expertise.diagnose(again.incident_id)
            diagnosed = lab.incident(again.incident_id)
            repair = diagnosed.repairs[0]
            recorded = json.dumps(
                [event.payload for event in diagnosed.events], ensure_ascii=False
            )
            lab.service.authorize_incident_repair(
                str(again.incident_id), _decision(repair.repair_id)
            )
            lab.observe(ObservationStatus.HEALTHY)
            [lead] = lab.service.list_experiences()["experiences"]
            checks += [
                (
                    "la commande libre ne devient jamais une réparation exécutable",
                    repair.known_repair is None
                    and repair.operation == "restart_service"
                    and lead["attempt_count"] == 1,
                ),
                (
                    "la piste est citée comme action à appliquer soi-même",
                    "Piste manuelle connue" in recorded
                    and "l’exécute jamais" in recorded,
                ),
            ]

            # Not followed by recovery: never offered as a lead.
            previous = incident_manual.MANUAL_SETTLE_SECONDS
            incident_manual.MANUAL_SETTLE_SECONDS = 0
            try:
                lab.incidents.close()
                lab = _build(lab.root, helper_installed=True)
                failing = lab.observe(ObservationStatus.UNHEALTHY)
                _declare(lab, failing, "Redémarrage de la box")
                lab.observe(ObservationStatus.UNHEALTHY)
                lab.observe(ObservationStatus.HEALTHY)
            finally:
                incident_manual.MANUAL_SETTLE_SECONDS = previous
            unconfirmed = lab.incident(failing.incident_id)
            checks.append(
                (
                    "action non suivie d'un retour sain : non confirmée, pas de piste",
                    unconfirmed.manual_actions[0].status == "unconfirmed"
                    and unconfirmed.experience_candidate is None,
                )
            )

            # Konoha, 28 September: the service fixed by hand recovered before
            # the declaration was sent, and the closed incident refused it.
            late = lab.observe(ObservationStatus.UNHEALTHY)
            lab.observe(ObservationStatus.HEALTHY)
            try:
                late_action = _declare(lab, late, "Redémarrage de dnsmasq à la main")
            except ValueError as error:
                late_action = None
                details["déclaration tardive"] = f"refusée : {error}"
            late_incident = lab.incident(late.incident_id)
            late_candidate = late_incident.experience_candidate
            checks.append(
                (
                    "déclaration juste après le retour sain : acceptée comme telle",
                    late_action is not None
                    and late_action.status == "confirmed"
                    and late_candidate is not None
                    and "déclarée après" in (late_candidate.caution or "")
                    and "ne prouve pas à elle seule" in (late_candidate.caution or ""),
                )
            )
            details["piste"] = f"« {COMMAND} » conservée comme note, jamais exécutée"
        finally:
            lab.incidents.close()
    details["portée"] = "Agent et SQLite locaux ; demande dnsmasq en répertoire temporaire"
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
