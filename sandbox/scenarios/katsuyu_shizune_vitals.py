"""Phase 5, lot 4: Katsuyu and Shizune vital states, without any incident.

Real Agent HTTP listeners (administration/worker and companion), real
Katsuyu worker loop and handlers over HTTP, real Vision application with
its Shizune bridge. The AI model and the age binary are simply absent or
present on disk; nothing on Konoha is touched.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import certifi
from fastapi.testclient import TestClient
from ohana_agent.api.http import AdministrationHTTPServer
from ohana_agent.api.service import AdministrationService
from ohana_agent.companions.repository import CompanionRepository
from ohana_agent.infrastructure.repository import InfrastructureConfigurationRepository
from ohana_agent.jobs.repository import DistributedJobRepository
from ohana_agent.tsunade.incidents import TsunadeIncidentRepository
from ohana_katsuyu.ai import AiInferenceHandler
from ohana_katsuyu.handlers import (
    BackupEncryptHandler,
    KatsuyuWorkspace,
    SystemHealthHandler,
)
from ohana_katsuyu.worker import AgentClient, KatsuyuWorker
from ohana_vision.administration import AgentCompanionClient
from ohana_vision.runtime import BackendRuntime
from ohana_vision.web import create_app
from ohana_vision.web.application_context import ApplicationContext

WORKER = "katsuyu-sandbox"
DEVICE = "iphone-sandbox"
ADMIN_TOKEN = "tsunade-sandbox"
WORKER_TOKEN = "katsuyu-sandbox-secret"
MODEL = b"sandbox model"
FAKE_PEM = "-----BEGIN CERTIFICATE-----\n" + "A" * 64 + "\n-----END CERTIFICATE-----"
INFRASTRUCTURE_YAML = """\
infrastructure:
  id: ohana-sandbox
  name: Ohana Sandbox
  environment: production
nodes: []
services: []
"""


def _paris(value: object) -> bool:
    return isinstance(value, str) and value.endswith(("+01:00", "+02:00"))


def _get(server: AdministrationHTTPServer, path: str) -> dict[str, Any]:
    host, port = server.address
    request = Request(
        f"http://{host}:{port}{path}",
        headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
    )
    with urlopen(request, timeout=5) as response:
        return json.load(response)


def _worker(server: AdministrationHTTPServer) -> dict[str, Any]:
    return _get(server, "/v1/jobs/workers")["workers"][0]


def _pair(companions: CompanionRepository) -> str:
    created = companions.create_pairing(
        {
            "protocol_version": 1,
            "device_id": DEVICE,
            "device_name": "iPhone Sandbox",
            "platform": "ios",
            "app_version": "sandbox",
        },
        tls_ca_sha256="a" * 64,
        tls_ca_certificate_pem=FAKE_PEM,
    )
    companions.approve_pairing(created.pairing_id)
    token = companions.poll_pairing(
        created.pairing_id,
        {"protocol_version": 1, "polling_secret": created.polling_secret},
    ).companion_token
    assert token is not None
    return token


def _incident_count(root: Path) -> int:
    connection = sqlite3.connect(root / "control.db")
    try:
        return connection.execute("SELECT COUNT(*) FROM tsunade_incidents").fetchone()[0]
    finally:
        connection.close()


def run() -> dict:
    checks: list[tuple[str, bool]] = []
    details: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-vitals-") as tmp:
        root = Path(tmp)
        (root / "infrastructure.yaml").write_text(INFRASTRUCTURE_YAML, encoding="utf-8")
        jobs = DistributedJobRepository(root / "jobs.db")
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
        try:
            incidents_before = _incident_count(root)
            _katsuyu(root, administration, jobs, checks, details)
            _shizune(root, administration, companion_listener, companions, checks, details)
            checks.append(
                (
                    "aucun incident ni réparation : l'absence reste informative",
                    _incident_count(root) == incidents_before,
                )
            )
        finally:
            administration.stop()
            companion_listener.stop()
            companions.close()
            incidents.close()
            jobs.close()
    details["portée"] = (
        "Agent HTTP, worker Katsuyu et pont Shizune de Vision réels ; "
        "modèle IA et age simulés par leur présence sur disque"
    )
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }


def _katsuyu(
    root: Path,
    administration: AdministrationHTTPServer,
    jobs: DistributedJobRepository,
    checks: list[tuple[str, bool]],
    details: dict[str, str],
) -> None:
    host, port = administration.address
    (root / "llama-server.exe").write_bytes(b"")
    model = root / "model.gguf"
    workspace = KatsuyuWorkspace(root / "workspace")
    worker = KatsuyuWorker(
        client=AgentClient(f"http://{host}:{port}", WORKER_TOKEN),
        worker_id=WORKER,
        handlers={
            "system.health": SystemHealthHandler(workspace),
            "backup.encrypt": BackupEncryptHandler(workspace, root / "age.exe"),
            "ai.inference": AiInferenceHandler(
                runtime=root / "llama-server.exe",
                model=model,
                model_id="ministral-sandbox",
                model_sha256=hashlib.sha256(MODEL).hexdigest(),
            ),
        },
        heartbeat_seconds=0.2,
        runtime_refresh_seconds=0,
    )
    worker.register()
    registered = _worker(administration)
    runtimes = registered.get("runtimes", {})
    checks += [
        (
            "Katsuyu annonce le runtime de chaque capacité qui en dépend",
            set(runtimes) == {"ai.inference", "backup.encrypt"},
        ),
        (
            "modèle IA absent et binaire age absent : « missing » avec la cause",
            runtimes.get("ai.inference", {}).get("detail") == "modèle IA absent"
            and runtimes.get("backup.encrypt", {}).get("state") == "missing",
        ),
        (
            "heure du rapport à l'heure de Paris",
            _paris(registered.get("runtimes_reported_at")),
        ),
    ]

    jobs.create(
        {
            "protocol_version": 1,
            "job_id": "55555555-5555-4555-8555-555555555555",
            "type": "system.health",
            "created_at": datetime.now().astimezone().isoformat(),
            "parameters": {},
            "timeout": 600,
        }
    )
    ran = worker.run_once()
    activity = {item["type"]: item for item in _worker(administration)["activity"]}
    health = activity.get("system.health", {})
    checks += [
        (
            "dernier job réussi par capacité, daté à Paris",
            ran and _paris(health.get("last_succeeded_at")),
        ),
        (
            "capacité jamais exécutée : aucune date inventée",
            activity.get("ai.inference", {}).get("last_succeeded_at") is None,
        ),
    ]

    model.write_bytes(MODEL)
    worker.run_once()
    after = _worker(administration)["runtimes"]["ai.inference"]
    checks.append(
        (
            "modèle déposé : le runtime IA passe à « unverified » sans redémarrage",
            after["state"] == "unverified",
        )
    )
    details["Katsuyu"] = (
        f"ai.inference={after['state']} ({after['detail']}), "
        f"backup.encrypt={runtimes.get('backup.encrypt', {}).get('state')}, "
        f"system.health réussi {health.get('last_succeeded_at')}"
    )


def _shizune(
    root: Path,
    administration: AdministrationHTTPServer,
    companion_listener: AdministrationHTTPServer,
    companions: CompanionRepository,
    checks: list[tuple[str, bool]],
    details: dict[str, str],
) -> None:
    token = _pair(companions)
    host, port = companion_listener.address
    runtime = BackendRuntime()
    vision = TestClient(
        create_app(
            ApplicationContext(
                runtime=runtime,
                observation_store=None,  # type: ignore[arg-type]
                timeline_engine=None,  # type: ignore[arg-type]
            ),
            companion_client=AgentCompanionClient(
                base_url=f"http://{host}:{port}",
                ca_certificate_file=Path(certifi.where()),
                timeout_seconds=3,
            ),
        )
    )
    session = {"Authorization": f"Bearer {token}", "X-Ohana-Companion-Id": DEVICE}
    unused = runtime.vitals()["shizune_gateway"]
    summary = vision.get("/api/shizune/summary", headers=session)
    available = runtime.vitals()["shizune_gateway"]
    devices = _get(administration, "/v1/companions")["devices"]
    last_seen = devices[0]["last_seen_at"] if devices else None
    checks += [
        (
            "passerelle Shizune : « unused » avant tout appel relayé",
            unused["state"] == "unused",
        ),
        (
            "synthèse Shizune relayée par Vision : passerelle « available »",
            summary.status_code == 200
            and available["state"] == "available"
            and _paris(available["last_success_at"]),
        ),
        (
            "dernière synchronisation de l'appareil connue de l'Agent, à Paris",
            _paris(last_seen),
        ),
    ]

    companion_listener.stop()
    down = vision.get("/api/shizune/summary", headers=session)
    failing = runtime.vitals()["shizune_gateway"]
    checks.append(
        (
            "Agent injoignable : passerelle « failing » avec la cause, réponse 502",
            down.status_code == 502
            and failing["state"] == "failing"
            and "indisponible" in (failing["last_failure"] or ""),
        )
    )
    details["Shizune"] = (
        f"dernière synchronisation {last_seen}, passerelle {failing['state']} "
        f"({failing['last_failure']})"
    )
