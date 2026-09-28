"""Vision detects a silent Agent without incoming events or an Agent API.

Real HTTP ingestion, SQLite, Vision UI and Chromium. Only Vision's monotonic
clock is advanced to avoid waiting five minutes. Browser polling is unchanged.
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

import uvicorn
from ohana_vision.runtime.agent_presence import AgentPresence
from ohana_vision.web.app import create_app
from ohana_vision.web.bootstrap import build_application_context
from playwright.sync_api import expect, sync_playwright
from starlette.staticfiles import StaticFiles


def run() -> dict:
    checks = []
    output = (
        Path(__file__).resolve().parents[1]
        / "runs"
        / (datetime.now(UTC).strftime("%Y%m%d-%H%M%SZ") + "-agent-silent")
    )
    output.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="ohana-agent-silent-") as tmp:
        context = build_application_context(database_path=Path(tmp) / "vision.db")
        seconds = [0.0]
        context.runtime.agent_presence = AgentPresence(timer=lambda: seconds[0])
        context.runtime.agent_presence.start()
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(128)
        base = f"http://127.0.0.1:{listener.getsockname()[1]}"
        app = create_app(context=context)
        shizune = Path(__file__).resolve().parents[3] / "Ohana-Shizune/Shizune/PWA"
        if not shizune.is_dir():
            shizune = Path(tmp) / "shizune"
            shizune.mkdir()
        for route in app.routes:
            if getattr(route, "name", None) == "shizune":
                route.app = StaticFiles(directory=shizune, html=True)
        server = uvicorn.Server(uvicorn.Config(app, log_level="warning"))
        thread = threading.Thread(
            target=lambda: asyncio.run(
                server.serve(sockets=[listener]), loop_factory=asyncio.SelectorEventLoop
            ),
            daemon=True,
        )
        thread.start()

        def request(path, payload=None):
            data = json.dumps(payload).encode() if payload else None
            query = urllib.request.Request(
                base + path, data=data, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(query, timeout=5) as response:
                return json.load(response)

        def presence():
            return request("/api/runtime/vitals")["agent"]

        try:
            deadline = time.monotonic() + 10
            while not server.started and time.monotonic() < deadline:
                time.sleep(0.025)
            checks.append(
                (
                    "Sans réception : en attente, jamais sain",
                    presence()["state"] == "waiting",
                )
            )
            payload = {
                "observation_id": str(uuid4()),
                "capability_id": "host.health",
                "service_id": "ohana-host",
                "node_id": "infra-01",
                "status": "healthy",
                "observed_at": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                "message": "État sain historique rejoué",
                "metadata": {
                    "host_health": {
                        "state": "healthy",
                        "hostname": "INFRA-01",
                        "reasons": [],
                    }
                },
            }
            request("/api/observations", payload)
            first = presence()
            checks.append(
                (
                    "Rejeu ancien : activité mesurée à la réception par Vision",
                    first["state"] == "active" and first["silence_seconds"] == 0,
                )
            )
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                page = browser.new_page(viewport={"width": 1440, "height": 1000})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(base + "/ui/#host")
                expect(page.locator("#host-state-label")).to_have_text("Sain")
                expect(page.locator("#agent-presence")).to_be_hidden()

                # No POST and no WebSocket event from now until the warning appears.
                seconds[0] = 301
                checks.append(
                    (
                        "Sans nouvelle observation : Vision constate le silence",
                        presence()["state"] == "silent",
                    )
                )
                expect(page.locator("#agent-presence-title")).to_have_text(
                    "Agent silencieux", timeout=20000
                )
                expect(page.locator("#agent-presence")).to_be_visible()
                expect(page.locator("#host-state-label")).to_have_text(
                    "État actuel inconnu"
                )
                page.screenshot(
                    path=str(output / "agent-silent-desktop.png"), full_page=True
                )
                checks.append(
                    (
                        "Page déjà ouverte : alerte et santé ancienne invalidée sans événement Agent",
                        True,
                    )
                )

                page.locator('[data-navigation-target="overview"]').click()
                expect(page.locator("#agent-presence")).to_be_visible()
                page.screenshot(
                    path=str(output / "agent-silent-overview.png"), full_page=True
                )
                page.set_viewport_size({"width": 390, "height": 844})
                expect(page.locator("#agent-presence")).to_be_visible()
                checks.append(
                    (
                        "Alerte globale visible sur mobile sans débordement",
                        page.evaluate(
                            "document.documentElement.scrollWidth <= window.innerWidth"
                        ),
                    )
                )
                page.screenshot(
                    path=str(output / "agent-silent-mobile.png"), full_page=True
                )

                # Duplicate delivery (old observed_at) proves transport activity only.
                request("/api/observations", payload)
                expect(page.locator("#agent-presence")).to_be_hidden(timeout=20000)
                checks.append(
                    (
                        "Retour de l'Agent : avertissement retiré automatiquement",
                        presence()["state"] == "active",
                    )
                )

                # An unreadable Vision endpoint is not evidence against the Agent.
                page.route(
                    "**/api/runtime/vitals",
                    lambda route: route.fulfill(status=503, body="unavailable"),
                )
                expect(page.locator("#agent-presence-title")).to_have_text(
                    "Surveillance de l’Agent indisponible", timeout=20000
                )
                checks.append(
                    (
                        "Erreur de lecture Vision : état inconnu, pas Agent silencieux",
                        True,
                    )
                )
                checks.append(("Aucune erreur JavaScript", not errors))
                browser.close()
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            listener.close()
            context.observation_store.close()
            context.incident_store.close()
    result = {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": {
            "captures": str(output),
            "limites": "Horloge monotone Vision avancée ; aucune panne réelle sur Konoha, aucune API Agent configurée.",
        },
    }
    (output / "report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result
