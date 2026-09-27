"""Phase 3, lots 1 and 2: history, citation and lifecycle of a known repair.

The dnsmasq repair saved on Konoha is reproduced four times through the real
Agent services and SQLite stores (the restart request stays in a temporary
directory). Each execution must be counted against the known repair with its
outcome, a repair Tsunade already knows must not ask to be saved again, and a
disabled known repair must no longer be offered nor counted.
"""

from __future__ import annotations

from ohana_agent.observation import ObservationStatus

from scenarios.supervised_repair_cycle import _build, _decision, _lab, _restart


def _repair_cycle(lab, *, healthy_after: bool = True):
    incident = lab.observe(ObservationStatus.UNHEALTHY)
    lab.expertise.diagnose(incident.incident_id)
    repair = lab.incident(incident.incident_id).repairs[0]
    try:
        lab.service.authorize_incident_repair(
            str(incident.incident_id), _decision(repair.repair_id)
        )
    except (LookupError, ValueError, OSError):
        pass
    if healthy_after:
        lab.observe(ObservationStatus.HEALTHY)
    lab.reload_request.unlink(missing_ok=True)
    return lab.incident(incident.incident_id)


def _known(lab):
    [experience] = lab.service.list_experiences()["experiences"]
    return experience


def run() -> dict:
    checks = []
    details = {}
    with _lab() as lab:
        try:
            first = _repair_cycle(lab)
            lab.service.confirm_incident_experience(
                str(first.incident_id),
                {"confirm": True, "source": "vision", "confirmed_by": "sandbox"},
            )
            saved = _known(lab)
            checks.append(
                (
                    "1re réparation enregistrée : 1 tentative, 1 réussite",
                    (saved["attempt_count"], saved["success_count"]) == (1, 1)
                    and saved["last_success_at"] is not None,
                )
            )

            lab = _restart(lab)
            second = _repair_cycle(lab)
            counted = _known(lab)
            checks += [
                (
                    "2e exécution comptée automatiquement après reprise SQLite",
                    (counted["attempt_count"], counted["success_count"]) == (2, 2),
                ),
                (
                    "réparation déjà connue : aucune nouvelle demande d'enregistrement",
                    second.repairs[0].status == "succeeded"
                    and second.experience_candidate is None,
                ),
                (
                    "la 2e proposition cite la réparation connue sur preuve confirmée",
                    (known := second.repairs[0].known_repair) is not None
                    and known.success_count == 1
                    and any("Même preuve" in item for item in known.criteria),
                ),
                (
                    "la demande d'autorisation (Vision, Shizune) cite son historique",
                    any(
                        "Réparation connue : 1 réussite(s)" in request.context
                        for request in lab.incidents.list_user_requests(
                            state="all"
                        ).requests
                    ),
                ),
            ]

            # Helper missing: the authorized execution fails immediately.
            lab.incidents.close()
            lab = _build(lab.root, helper_installed=False)
            third = _repair_cycle(lab, healthy_after=False)
            failed = _known(lab)
            checks.append(
                (
                    "3e exécution en échec comptée : 3 tentatives, 1 échec",
                    third.repairs[0].status == "failed"
                    and (failed["attempt_count"], failed["failure_count"]) == (3, 1)
                    and failed["last_failure_at"] is not None,
                )
            )
            lab.observe(ObservationStatus.HEALTHY)

            lab.incidents.close()
            lab = _build(lab.root, helper_installed=True)
            lab.service.set_experience_state(
                failed["experience_id"], {"state": "disabled", "reason": "sandbox"}
            )
            fourth = lab.observe(ObservationStatus.UNHEALTHY)
            lab.expertise.diagnose(fourth.incident_id)
            offered = lab.incidents.matching_experiences(lab.incident(fourth.incident_id))
            repair = lab.incident(fourth.incident_id).repairs[0]
            lab.service.authorize_incident_repair(
                str(fourth.incident_id), _decision(repair.repair_id)
            )
            lab.observe(ObservationStatus.HEALTHY)
            disabled = _known(lab)
            checks += [
                (
                    "réparation désactivée : plus proposée ni citée",
                    offered == [] and repair.known_repair is None,
                ),
                (
                    "réparation désactivée : exécution du catalogue non comptée",
                    disabled["state"] == "disabled" and disabled["attempt_count"] == 3,
                ),
                (
                    "statistiques : aucune réparation connue active",
                    lab.incidents.statistics()["learned_repair_count"] == 0,
                ),
            ]
            details["historique"] = (
                f"{disabled['attempt_count']} tentatives, "
                f"{disabled['success_count']} réussites, "
                f"{disabled['failure_count']} échec ; état {disabled['state']}"
            )
        finally:
            # The lab is rebuilt on the way: always release the latest store.
            lab.incidents.close()
    details["portée"] = "Agent et SQLite locaux ; demande dnsmasq en répertoire temporaire"
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
