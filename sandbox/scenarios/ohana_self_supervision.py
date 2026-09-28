"""Phase 5, lot 5: the "Ohana" view in Vision, fed by real components.

Real Agent HTTP listeners (administration/worker, companion), real Katsuyu
worker loop, real Vision server (uvicorn, SQLite) with its administration
and Shizune clients, real Agent vitals and Vision probe objects, Chromium.
Only the Agent's monotonic vitals clock and the job repository clock are
advanced; nothing on Konoha is touched.
"""

from __future__ import annotations

import asyncio
import json
import socket
import tempfile
import threading
import time
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import certifi
import uvicorn
from ohana_agent.api.http import AdministrationHTTPServer
from ohana_agent.api.service import AdministrationService
from ohana_agent.companions.repository import CompanionRepository
from ohana_agent.infrastructure.repository import InfrastructureConfigurationRepository
from ohana_agent.jobs.repository import DistributedJobRepository
from ohana_agent.runtime.vision_probe import VisionVitalsProbe
from ohana_agent.runtime.vitals import AgentVitals, stale_components
from ohana_agent.tsunade.incidents import TsunadeIncidentRepository
from ohana_katsuyu.ai import AiInferenceHandler
from ohana_katsuyu.handlers import KatsuyuWorkspace, SystemHealthHandler
from ohana_katsuyu.worker import AgentClient, KatsuyuWorker
from ohana_vision.administration import AgentCompanionClient
from ohana_vision.administration.client import AgentAdministrationClient
from ohana_vision.web.app import create_app
from ohana_vision.web.bootstrap import build_application_context
from playwright.sync_api import expect, sync_playwright
from starlette.staticfiles import StaticFiles

from scenarios.katsuyu_shizune_vitals import (
    ADMIN_TOKEN,
    FAKE_PEM,
    INFRASTRUCTURE_YAML,
    WORKER,
    WORKER_TOKEN,
    _pair,
)

DEVICE = "iphone-sandbox"


class Clock:
    def __init__(self) -> None:
        self.offset = timedelta()

    def __call__(self) -> datetime:
        return datetime.now(UTC) + self.offset


def _serve_vision(root: Path, admin_url: str, companion_url: str):
    token_file = root / "agent.token"
    token_file.write_text(ADMIN_TOKEN, encoding="utf-8")
    context = build_application_context(database_path=root / "vision.db")
    app = create_app(
        context=context,
        administration_client=AgentAdministrationClient(
            base_url=admin_url, token_file=token_file, timeout_seconds=3
        ),
        companion_client=AgentCompanionClient(
            base_url=companion_url,
            ca_certificate_file=Path(certifi.where()),
            timeout_seconds=3,
        ),
    )
    shizune = Path(__file__).resolve().parents[3] / "Ohana-Shizune/Shizune/PWA"
    if shizune.is_dir():
        for route in app.routes:
            if getattr(route, "name", None) == "shizune":
                route.app = StaticFiles(directory=shizune, html=True)
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(128)
    server = uvicorn.Server(uvicorn.Config(app, log_level="warning"))
    thread = threading.Thread(
        target=lambda: asyncio.run(
            server.serve(sockets=[listener]), loop_factory=asyncio.SelectorEventLoop
        ),
        daemon=True,
    )
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.025)
    return context, server, thread, listener, f"http://127.0.0.1:{listener.getsockname()[1]}"


def _http(base: str, path: str, payload=None, headers=None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        base + path,
        data=data,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.load(response), (time.perf_counter() - started) * 1000


def _host_health(vitals: AgentVitals, probe: VisionVitalsProbe) -> dict:
    components = vitals.snapshot()
    stale = stale_components(components)
    return {
        "observation_id": str(uuid4()),
        "capability_id": "host.health",
        "service_id": "ohana-host",
        "node_id": "infra-01",
        "status": "degraded" if stale else "healthy",
        "observed_at": datetime.now(UTC).isoformat(),
        "message": "Santé de l'hôte Sandbox",
        "metadata": {
            "host_health": {
                "state": "degraded" if stale else "healthy",
                "hostname": "INFRA-01",
                "reasons": ["agent_components_stale"] if stale else [],
                "agent_components": list(components),
                "stale_agent_components": list(stale),
                "vision": probe.check_now(),
            }
        },
    }


def _card(page, component: str):
    return page.locator(f'.ohana-component[data-component="{component}"]')


def run() -> dict:
    checks: list[tuple[str, bool]] = []
    details: dict[str, str] = {}
    output = (
        Path(__file__).resolve().parents[1]
        / "runs"
        / (datetime.now(UTC).strftime("%Y%m%d-%H%M%SZ") + "-ohana-self-supervision")
    )
    output.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-self-") as tmp:
        root = Path(tmp)
        (root / "infrastructure.yaml").write_text(INFRASTRUCTURE_YAML, encoding="utf-8")
        clock = Clock()
        jobs = DistributedJobRepository(root / "jobs.db", clock=clock)
        incidents = TsunadeIncidentRepository(root / "control.db")
        companions = CompanionRepository(root / "companions.db")
        service = AdministrationService(
            infrastructure_repository=InfrastructureConfigurationRepository(
                root / "infrastructure.yaml"
            ),
            job_repository=jobs,
            incident_repository=incidents,
            companion_repository=companions,
            companion_ca_sha256="a" * 64,
            companion_ca_certificate_pem=FAKE_PEM,
        )
        administration = AdministrationHTTPServer(
            service=service, token=ADMIN_TOKEN, worker_token=WORKER_TOKEN, port=0
        )
        companion_listener = AdministrationHTTPServer(
            service=service, token=ADMIN_TOKEN, companion_only=True, port=0
        )
        administration.start()
        companion_listener.start()
        admin_host, admin_port = administration.address
        companion_host, companion_port = companion_listener.address
        context, server, thread, listener, base = _serve_vision(
            root,
            f"http://{admin_host}:{admin_port}",
            f"http://{companion_host}:{companion_port}",
        )
        try:
            # Katsuyu registers, reports a missing AI model and runs one job.
            (root / "llama-server.exe").write_bytes(b"")
            worker = KatsuyuWorker(
                client=AgentClient(f"http://{admin_host}:{admin_port}", WORKER_TOKEN),
                worker_id=WORKER,
                handlers={
                    "system.health": SystemHealthHandler(
                        KatsuyuWorkspace(root / "workspace")
                    ),
                    "ai.inference": AiInferenceHandler(
                        runtime=root / "llama-server.exe",
                        model=root / "model.gguf",
                        model_id="ministral-sandbox",
                        model_sha256="0" * 64,
                    ),
                },
                heartbeat_seconds=0.2,
                runtime_refresh_seconds=0,
            )
            worker.register()
            jobs.create(
                {
                    "protocol_version": 1,
                    "job_id": str(uuid4()),
                    "type": "system.health",
                    "created_at": clock().isoformat(),
                    "parameters": {},
                    "timeout": 600,
                }
            )
            worker.run_once()

            # Real Agent vitals and a real probe of this Vision server.
            ticks = [0.0]
            vitals = AgentVitals(monotonic_clock=lambda: ticks[0])
            for name, label in (
                ("scheduler", "Planificateur"),
                ("vision_delivery", "Livraison à Vision"),
                ("tsunade", "Tsunade (incidents)"),
            ):
                vitals.declare(name, label=label, max_silence_seconds=300)
                vitals.beat(name)
            probe = VisionVitalsProbe(base + "/api/runtime/vitals", timeout_seconds=3)
            _http(base, "/api/observations", _host_health(vitals, probe))

            # Shizune synchronises through Vision's bridge.
            token = _pair(companions)
            _http(
                base,
                "/api/shizune/summary",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Ohana-Companion-Id": DEVICE,
                },
            )
            _, vitals_ms = _http(base, "/api/runtime/vitals")
            _, workers_ms = _http(base, "/api/administration/workers")

            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                page = browser.new_page(viewport={"width": 1440, "height": 1000})
                errors: list[str] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(base + "/ui/#ohana")
                expect(_card(page, "shizune")).to_have_attribute("data-state", "healthy")
                states = {
                    name: _card(page, name).get_attribute("data-state")
                    for name in ("agent", "vision", "katsuyu", "shizune")
                }
                checks += [
                    (
                        "vue Ohana : Agent, Vision et Shizune opérationnels",
                        states["agent"] == states["vision"] == "healthy"
                        and states["shizune"] == "healthy",
                    ),
                    (
                        "Agent : composants internes et dernière activité affichés",
                        "Planificateur" in _card(page, "agent").inner_text()
                        and "Dernière activité" in _card(page, "agent").inner_text(),
                    ),
                    (
                        "Vision : vu par l'Agent (sonde réelle) « Disponible »",
                        "Disponible" in _card(page, "vision").inner_text(),
                    ),
                    (
                        "Katsuyu connecté mais modèle IA absent : « À surveiller » avec la cause",
                        states["katsuyu"] == "degraded"
                        and "Analyse IA locale" in _card(page, "katsuyu").inner_text()
                        and "modèle IA absent" in _card(page, "katsuyu").inner_text(),
                    ),
                    (
                        "Katsuyu : dernier succès de la santé du PC affiché",
                        "Dernier succès" in _card(page, "katsuyu").inner_text(),
                    ),
                    (
                        "Shizune : dernière synchronisation de l'appareil affichée",
                        "Dernière synchronisation" in _card(page, "shizune").inner_text(),
                    ),
                ]
                page.screenshot(path=str(output / "ohana-desktop.png"), full_page=True)

                # A silent internal component, published through host.health.
                ticks[0] = 301
                vitals.beat("scheduler")
                vitals.beat("vision_delivery")
                _http(base, "/api/observations", _host_health(vitals, probe))
                # Bubule goes to sleep: no contact for more than the 30 s window.
                clock.offset = timedelta(seconds=90)
                page.locator("#refresh-button").click()
                expect(_card(page, "agent")).to_have_attribute(
                    "data-state", "degraded", timeout=20000
                )
                expect(_card(page, "katsuyu")).to_have_attribute("data-state", "offline")
                checks += [
                    (
                        "composant muet : carte Agent « À surveiller » nommant Tsunade",
                        "Tsunade (incidents)" in _card(page, "agent").inner_text(),
                    ),
                    (
                        "PC Katsuyu éteint : « Hors ligne », présenté comme normal",
                        "normal" in _card(page, "katsuyu").inner_text(),
                    ),
                ]
                page.screenshot(path=str(output / "ohana-degraded.png"), full_page=True)

                # The Agent administration API goes away: other cards remain.
                administration.stop()
                page.locator("#refresh-button").click()
                expect(_card(page, "katsuyu")).to_contain_text(
                    "indisponible", timeout=20000
                )
                checks.append(
                    (
                        "API Agent indisponible : Katsuyu inconnu, les autres cartes restent lisibles",
                        _card(page, "katsuyu").get_attribute("data-state") == "unknown"
                        and _card(page, "vision").get_attribute("data-state") == "healthy"
                        and _card(page, "agent").get_attribute("data-state") == "degraded",
                    )
                )
                page.set_viewport_size({"width": 390, "height": 844})
                checks.append(
                    (
                        "mobile : quatre cartes sans débordement horizontal",
                        page.locator(".ohana-component").count() == 4
                        and page.evaluate(
                            "document.documentElement.scrollWidth <= window.innerWidth"
                        ),
                    )
                )
                page.screenshot(path=str(output / "ohana-mobile.png"), full_page=True)
                checks.append(("aucune erreur JavaScript", not errors))
                browser.close()
            checks.append(
                (
                    "aucun incident Tsunade créé par l'auto-supervision",
                    not incidents.list(state="all"),
                )
            )
            details["coût"] = (
                f"/api/runtime/vitals {vitals_ms:.1f} ms, "
                f"/api/administration/workers {workers_ms:.1f} ms (poste de dev)"
            )
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            listener.close()
            companion_listener.stop()
            try:
                administration.stop()
            except Exception:  # noqa: BLE001 - already stopped by the scenario.
                pass
            context.observation_store.close()
            context.incident_store.close()
            companions.close()
            incidents.close()
            jobs.close()
    details["captures"] = str(output)
    details["limites"] = (
        "horloges des vitaux et des jobs avancées ; métriques de l'hôte "
        "simulées ; aucune panne réelle sur Konoha"
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
