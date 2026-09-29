"""Phase 3 hardening: finer incident comparison and history in Vision.

Real Agent HTTP administration listener with the real Tsunade incident
repository, filled with replayed host.health episodes of INFRA-01 (two
stopped Vision, one full disk, one repaired unit), a real Vision server and
Chromium: the "Historique" view (filters, equipment sheet, 30-day timeline)
and "Incidents semblables" on the open incident card.
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from ohana_agent.api.http import AdministrationHTTPServer
from ohana_agent.api.service import AdministrationService
from ohana_agent.infrastructure.repository import InfrastructureConfigurationRepository
from ohana_agent.observation.observation import Observation
from ohana_agent.observation.observation_status import ObservationStatus
from ohana_agent.tsunade.incidents import TsunadeIncidentRepository
from playwright.sync_api import expect, sync_playwright

from scenarios.katsuyu_shizune_vitals import ADMIN_TOKEN, INFRASTRUCTURE_YAML
from scenarios.ohana_self_supervision import _serve_vision

PARIS = ZoneInfo("Europe/Paris")
NOW = datetime.now(PARIS)


def _host(at: datetime, status: ObservationStatus, reasons: list[str]) -> Observation:
    return Observation(
        node="infra-01",
        service="ohana-host",
        capability="host.health",
        status=status,
        success=status is ObservationStatus.HEALTHY,
        message=", ".join(reasons) or "Host healthy",
        source="host-health",
        timestamp=at,
        metadata={
            "target_type": "device",
            "device_id": "infra-01",
            "host_health": {"reasons": reasons},
        },
    )


def _episode(repository, days_ago: float, reasons: list[str], minutes: int) -> str:
    at = NOW - timedelta(days=days_ago)
    incident = repository.process(_host(at, ObservationStatus.UNHEALTHY, reasons))
    repository.process(
        _host(at + timedelta(minutes=minutes), ObservationStatus.HEALTHY, [])
    )
    return str(incident.incident_id)


def run() -> dict:
    checks: list[tuple[str, bool]] = []
    details: dict[str, object] = {}
    output = (
        Path(__file__).resolve().parents[1]
        / "runs"
        / (datetime.now(PARIS).strftime("%Y%m%d-%H%M%S") + "-incident-history")
    )
    output.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-history-") as tmp:
        root = Path(tmp)
        (root / "infrastructure.yaml").write_text(INFRASTRUCTURE_YAML, encoding="utf-8")
        incidents = TsunadeIncidentRepository(root / "control.db")
        vision_before = _episode(incidents, 25, ["vision_http_unavailable"], 7)
        _episode(incidents, 12, ["disk_critical"], 90)
        repaired = _episode(incidents, 6, ["systemd_units_failed"], 3)
        incidents._connection.execute(
            """INSERT INTO tsunade_repairs (repair_id, incident_id, operation,
            target, risk, status, proposed_at, executed_at) VALUES (?, ?,
            'restart_service', 'dnsmasq.service', 'low', 'succeeded', ?, ?)""",
            (
                str(uuid4()),
                repaired,
                (NOW - timedelta(days=6)).isoformat(),
                (NOW - timedelta(days=6) + timedelta(minutes=1)).isoformat(),
            ),
        )
        incidents._connection.commit()
        # Vision is down again now: the open incident of the Tsunade page.
        current = incidents.process(
            _host(NOW, ObservationStatus.UNHEALTHY, ["vision_http_unavailable"])
        )
        service = AdministrationService(
            infrastructure_repository=InfrastructureConfigurationRepository(
                root / "infrastructure.yaml"
            ),
            incident_repository=incidents,
        )
        administration = AdministrationHTTPServer(
            service=service, token=ADMIN_TOKEN, worker_token="w" * 32, port=0
        )
        administration.start()
        host, port = administration.address
        context, server, thread, listener, base = _serve_vision(
            root, f"http://{host}:{port}", f"http://{host}:{port}"
        )
        try:
            similar = service.read_similar_incidents(str(current.incident_id))
            details["semblables (API)"] = [
                (item["incident_id"] == vision_before, item["similarity"]["score"])
                for item in similar["similar"]
            ]
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                page = browser.new_page(viewport={"width": 1440, "height": 1000})
                errors: list[str] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(base + "/ui/#history")
                table = page.locator(".history-table tbody tr")
                expect(table.first).to_be_visible(timeout=20000)
                checks.append(
                    (
                        "Historique : les quatre incidents, du plus récent au plus ancien",
                        table.count() == 4
                        and "En cours" in table.nth(0).inner_text()
                        and "Réparé (vérifié)" in table.nth(1).inner_text(),
                    )
                )
                page.select_option('[data-history-filter="outcome"]', "repaired")
                expect(table).to_have_count(1, timeout=10000)
                checks.append(
                    (
                        "filtre « Réparé » : seul l'incident réparé reste",
                        "systemd_units_failed" in table.first.inner_text(),
                    )
                )
                page.select_option('[data-history-filter="outcome"]', "")
                expect(table).to_have_count(4, timeout=10000)
                page.locator("[data-history-equipment]").first.click()
                sheet = page.locator(".history-sheet")
                expect(sheet).to_be_visible(timeout=10000)
                checks.append(
                    (
                        "fiche INFRA-01 : incidents, durée cumulée et réparation réussie",
                        "4 dont 1 en cours" in sheet.inner_text()
                        and "100" in sheet.inner_text(),
                    )
                )
                bars = page.locator(".history-timeline__track .history-timeline__bar")
                checks.append(
                    (
                        "frise 30 jours : une barre par incident, un point de réparation",
                        bars.count() == 4
                        and page.locator(
                            ".history-timeline__track .history-timeline__repair"
                        ).count()
                        == 1,
                    )
                )
                page.screenshot(path=str(output / "history.png"), full_page=True)

                page.goto(base + "/ui/#incidents")
                button = page.locator(
                    f'[data-tsunade-similar="{current.incident_id}"]'
                )
                expect(button).to_be_visible(timeout=20000)
                button.click()
                block = page.locator(".incident-similar")
                expect(block).to_contain_text("ressemblance", timeout=10000)
                text = block.inner_text()
                checks.append(
                    (
                        "incident ouvert : l'arrêt de Vision de J-25 est semblable, "
                        "le disque plein (plus récent) ne l'est pas",
                        "vision_http_unavailable" in text
                        and "disk_critical" not in text
                        and "pas une cause" in text,
                    )
                )
                page.screenshot(path=str(output / "similar.png"), full_page=True)
                page.set_viewport_size({"width": 390, "height": 844})
                page.goto(base + "/ui/#history")
                expect(table.first).to_be_visible(timeout=20000)
                checks.append(
                    (
                        "mobile : pas de débordement horizontal de la page",
                        page.evaluate(
                            "document.documentElement.scrollWidth <= window.innerWidth"
                        ),
                    )
                )
                page.screenshot(path=str(output / "history-mobile.png"), full_page=True)
                checks.append(("aucune erreur JavaScript", not errors))
                browser.close()
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            listener.close()
            administration.stop()
            context.observation_store.close()
            context.incident_store.close()
            incidents.close()
    details["captures"] = str(output)
    result = {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
    (output / "report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return result
