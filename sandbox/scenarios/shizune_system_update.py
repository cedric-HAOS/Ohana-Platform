"""Shizune checks and starts INFRA-01's system update.

Real Shizune PWA in Chromium (iPhone viewport), real Vision gateway, real Agent
companion listener, real administration service and real update requester.
The apt reading is a controlled state and ``systemctl`` is simulated: no root
helper runs. The companion never chooses a package or an option, and nothing
restarts the machine.
"""

from __future__ import annotations

import json
import tempfile
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

from ohana_agent.api.http import AdministrationHTTPServer
from ohana_agent.api.service import AdministrationService
from ohana_agent.companions.repository import CompanionRepository
from ohana_agent.host.system_updates import SystemUpdateRequester
from ohana_agent.infrastructure.repository import InfrastructureConfigurationRepository
from ohana_agent.tsunade.incidents import TsunadeIncidentRepository
from playwright.sync_api import expect, sync_playwright

from scenarios.katsuyu_shizune_vitals import (
    ADMIN_TOKEN,
    DEVICE,
    FAKE_PEM,
    INFRASTRUCTURE_YAML,
    _pair,
)
from scenarios.ohana_self_supervision import _serve_vision

MONOTONIC_STAMP = "5000000"


def _post(base: str, path: str, session: dict[str, str]) -> tuple[int, dict]:
    request = urllib.request.Request(
        base + path,
        data=b"{}",
        method="POST",
        headers={"Content-Type": "application/json", **session},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def run() -> dict:
    checks: list[tuple[str, bool]] = []
    details: dict[str, str] = {}
    output = (
        Path(__file__).resolve().parents[1]
        / "runs"
        / (datetime.now(UTC).strftime("%Y%m%d-%H%M%SZ") + "-shizune-system-update")
    )
    output.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-shizune-update-") as tmp:
        root = Path(tmp)
        (root / "infrastructure.yaml").write_text(INFRASTRUCTURE_YAML, encoding="utf-8")

        # What apt would say, and what the root helpers would report.
        state = {
            "status": "stale_lists",
            "message": "Les listes de paquets sont périmées : les mises à jour "
            "en attente ne sont pas connues.",
            "pending_count": 5,
            "security_count": 2,
            "kernel_pending": False,
            "packages": [{"name": "openssl-sandbox", "security": True}],
            "packages_truncated": False,
            "held_back": [],
            "lists_refreshed_at": "2026-10-09T15:40:00+02:00",
            "lists_age_days": 32.0,
            "lists_stale": True,
            "reboot_required": False,
            "reboot_packages": [],
            "last_apt_run": None,
            "read_at": datetime.now(UTC).isoformat(),
        }
        helpers = {"refresh": "never", "upgrade": "never"}
        systemd = root / "systemd"
        systemd.mkdir()
        for stem in ("system-refresh", "system-upgrade"):
            (systemd / f"ohana-{stem}.path").write_text("", encoding="utf-8")
        systemctl = root / "systemctl"
        systemctl.write_text("", encoding="utf-8")

        def fake_systemctl(command, **_kwargs):
            run_state = helpers["refresh" if "refresh" in command[2] else "upgrade"]
            started = "0" if run_state == "never" else MONOTONIC_STAMP
            return SimpleNamespace(
                stdout=(
                    f"ActiveState={'activating' if run_state == 'running' else 'inactive'}\n"
                    f"Result={'exit-code' if run_state == 'failed' else 'success'}\n"
                    f"ExecMainStartTimestampMonotonic={started}\n"
                    f"ExecMainExitTimestampMonotonic="
                    f"{started if run_state in {'succeeded', 'failed'} else '0'}\n"
                ),
                returncode=0,
            )

        incidents = TsunadeIncidentRepository(root / "control.db")
        companions = CompanionRepository(root / "companions.db")
        service = AdministrationService(
            infrastructure_repository=InfrastructureConfigurationRepository(
                root / "infrastructure.yaml"
            ),
            incident_repository=incidents,
            companion_repository=companions,
            companion_ca_sha256="a" * 64,
            companion_ca_certificate_pem=FAKE_PEM,
            system_updates_reader=lambda: dict(state),
            system_update_requester=SystemUpdateRequester(
                request_directory=root / "run",
                systemd_directory=systemd,
                systemctl_path=systemctl,
                runner=fake_systemctl,
            ),
        )
        companion_listener = AdministrationHTTPServer(
            service=service, token=ADMIN_TOKEN, companion_only=True, port=0
        )
        companion_listener.start()
        host, port = companion_listener.address
        context, server, thread, listener, base = _serve_vision(
            root, "http://127.0.0.1:9", f"http://{host}:{port}"
        )

        def requests() -> list[str]:
            directory = root / "run"
            return sorted(path.name for path in directory.iterdir()) if directory.is_dir() else []

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                page = browser.new_page(viewport={"width": 390, "height": 844})
                errors: list[str] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                app = page.locator("#app")

                # The real pairing, approved on the Agent as Vision would.
                page.goto(base + "/shizune/")
                page.get_by_role("button", name="Associer cet iPhone").click()
                expect(page.locator(".pairing-code")).to_be_visible()
                companions.approve_pairing(companions.list_pairings().pairings[0].pairing_id)
                page.get_by_role("button", name="J’ai approuvé l’association").click()
                entry = page.get_by_role("button", name="Mise à jour d’INFRA-01 →")
                expect(entry).to_be_visible()

                with page.expect_response("**/api/shizune/system/updates") as reading:
                    entry.click()
                document = reading.value.json()
                expect(app).to_contain_text("Les listes de paquets sont périmées")
                checks += [
                    (
                        "Shizune lit l'état par la passerelle Vision et le listener compagnon",
                        reading.value.status == 200 and document["schema_version"] == 1
                        and document["pending_count"] == 5,
                    ),
                    (
                        "ni liste de paquets ni historique apt dans la réponse compagnon",
                        not {"packages", "held_back", "reboot_packages", "last_apt_run"}
                        & set(document)
                        and "openssl-sandbox" not in app.inner_text(),
                    ),
                    (
                        "listes périmées : vérification proposée, mise à jour non proposée",
                        page.get_by_role("button", name="Vérifier maintenant").is_visible()
                        and page.get_by_role("button", name="Mettre à jour").count() == 0,
                    ),
                ]
                page.screenshot(path=str(output / "01-listes-perimees.png"))

                # Check now: one request for the helper, then its progress and result.
                page.get_by_role("button", name="Vérifier maintenant").click()
                expect(app).to_contain_text("Vérification demandée")
                checks.append(
                    (
                        "« Vérifier maintenant » écrit la seule demande d'actualisation",
                        requests() == ["system-refresh.request"],
                    )
                )
                helpers["refresh"] = "running"
                expect(app).to_contain_text(
                    "Actualisation des listes en cours", timeout=20000
                )
                checks.append(
                    (
                        "pendant l'actualisation : avancement affiché, aucun bouton",
                        page.get_by_role("button", name="Vérifier maintenant").count() == 0
                        and page.get_by_role("button", name="Mettre à jour").count() == 0,
                    )
                )
                helpers["refresh"] = "succeeded"
                state.update(
                    status="security_updates",
                    message="2 mise(s) à jour de sécurité en attente.",
                    lists_stale=False,
                    lists_age_days=0.0,
                    lists_refreshed_at=datetime.now(UTC).isoformat(),
                )
                upgrade = page.get_by_role("button", name="Mettre à jour")
                expect(upgrade).to_be_visible(timeout=20000)
                expect(app).to_contain_text("5 paquets en attente, dont 2 de sécurité")
                expect(app).to_contain_text("Actualisation des listes : réussie")
                page.screenshot(path=str(output / "02-mises-a-jour-en-attente.png"))

                # Upgrade: nothing is requested before the confirmation.
                upgrade.click()
                expect(app).to_contain_text("Installer 5 mises à jour sur INFRA-01 ?")
                expect(app).to_contain_text("INFRA-01 n’est jamais redémarré")
                page.screenshot(path=str(output / "03-confirmation.png"))
                checks.append(
                    (
                        "« Mettre à jour » demande une confirmation avant toute demande",
                        requests() == ["system-refresh.request"],
                    )
                )
                page.get_by_role("button", name="Annuler").click()
                expect(upgrade).to_be_visible()
                checks.append(
                    ("« Annuler » n'écrit rien", requests() == ["system-refresh.request"])
                )
                upgrade.click()
                page.get_by_role("button", name="Confirmer").click()
                expect(app).to_contain_text("Mise à jour demandée")
                checks.append(
                    (
                        "« Confirmer » écrit la demande de mise à jour pour l'assistant",
                        requests() == ["system-refresh.request", "system-upgrade.request"],
                    )
                )
                helpers["upgrade"] = "running"
                expect(app).to_contain_text(
                    "Installation des mises à jour en cours", timeout=20000
                )
                session = {
                    "Authorization": f"Bearer {_pair(companions)}",
                    "X-Ohana-Companion-Id": DEVICE,
                }
                busy_status, busy = _post(base, "/api/shizune/system/updates/apply", session)
                checks.append(
                    (
                        "pendant l'installation : une seconde demande est ignorée",
                        busy_status == 200 and busy.get("busy") is True
                        and busy.get("started") is False,
                    )
                )
                helpers["upgrade"] = "succeeded"
                state.update(
                    status="up_to_date",
                    message="Le système est à jour.",
                    pending_count=0,
                    security_count=0,
                )
                expect(app).to_contain_text("Le système est à jour.", timeout=20000)
                expect(app).to_contain_text("Installation des mises à jour : réussie")
                page.screenshot(path=str(output / "04-a-jour.png"))
                checks += [
                    (
                        "système à jour : la mise à jour n'est plus proposée",
                        page.get_by_role("button", name="Mettre à jour").count() == 0
                        and page.get_by_role("button", name="Vérifier maintenant").is_visible(),
                    ),
                    (
                        "aucun débordement horizontal sur l'écran d'un iPhone",
                        page.evaluate(
                            "document.documentElement.scrollWidth <= window.innerWidth"
                        ),
                    ),
                    ("aucune erreur JavaScript dans la PWA", not errors),
                ]
                browser.close()

            # The guards live in the Agent, whatever the client sends.
            nothing_status, nothing = _post(base, "/api/shizune/system/updates/apply", session)
            unknown_status, _ = _post(base, "/api/shizune/system/updates/reboot", session)
            anonymous_status, _ = _post(base, "/api/shizune/system/updates/apply", {})
            hidden_status, _ = _post(
                f"http://{host}:{port}", "/v1/system/updates/refresh", {}
            )
            checks += [
                (
                    "rien en attente : l'Agent refuse et Shizune reçoit le motif",
                    nothing_status == 422 and "Aucune mise à jour" in str(nothing),
                ),
                (
                    "toute autre action est refusée par la passerelle",
                    unknown_status == 422,
                ),
                (
                    "sans session compagnon : refus, à la passerelle comme au listener",
                    anonymous_status == 401 and hidden_status == 401,
                ),
                (
                    "au total deux demandes écrites, aucune exécutée par l'Agent",
                    requests() == ["system-refresh.request", "system-upgrade.request"],
                ),
            ]
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            listener.close()
            companion_listener.stop()
            context.observation_store.close()
            context.incident_store.close()
            companions.close()
            incidents.close()
    details["captures"] = str(output)
    details["portée"] = (
        "PWA Shizune, passerelle Vision, listener compagnon et service "
        "d'administration réels ; lecture apt et systemctl simulés ; aucun "
        "assistant root, aucun accès production"
    )
    result = {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
    (output / "report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result
