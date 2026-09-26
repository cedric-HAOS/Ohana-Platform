"""Real HTTPS worker, local llama.cpp inference and browser-driven Vision cycle."""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import socket
import subprocess
import sys
from collections import Counter
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from time import monotonic, sleep
from uuid import uuid4
from zoneinfo import ZoneInfo

import uvicorn
from ohana_agent.api.http import AdministrationHTTPServer
from ohana_agent.api.service import AdministrationService
from ohana_agent.host.dhcp import DnsmasqDHCPRepository
from ohana_agent.infrastructure.repository import InfrastructureConfigurationRepository
from ohana_agent.jobs.log_sources import LogSourceBroker
from ohana_agent.jobs.repository import DistributedJobRepository
from ohana_agent.observation import Observation, ObservationStatus
from ohana_agent.plugins.backup.config import BackupConfig
from ohana_agent.tsunade.expertise import TsunadeExpertiseService
from ohana_agent.tsunade.incidents import TsunadeIncidentRepository
from ohana_agent.tsunade.local_time import paris_now
from ohana_vision.configuration import ApplicationConfiguration
from ohana_vision.web.bootstrap import build_application
from playwright.sync_api import expect, sync_playwright
from starlette.staticfiles import StaticFiles
from scenarios._support import NoProbes
from scenarios.supervised_repair_cycle import DnsmasqStopped
from ohana_agent.tsunade.incident_summary import incident_assessment

from integration.lifecycle import certificate, stop_worker

DEFAULT_MODEL = "Ministral-3-14B-Reasoning-2512-Q4_K_M.gguf"
DEFAULT_SHA256 = "fe08ca2158cd7438211ec6a4e5256d31bc980f016e3f5b635fe91fe6848d461c"


class ObservedServer(AdministrationHTTPServer):
    """Observe response status without logging headers, tokens or journal bodies."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.responses = Counter()

    async def _dispatch(self, request):
        # Agent 1.30 serves its listeners with aiohttp: the former
        # http.server handler class no longer exists.
        response = await super()._dispatch(request)
        path = request.raw_path.split("?", 1)[0]
        self.responses[(request.method, path, response.status)] += 1
        return response


def _wait(label, predicate, *, timeout, worker=None, page=None):
    deadline = monotonic() + timeout
    next_update = monotonic() + 15
    while monotonic() < deadline:
        value = predicate()
        if value:
            return value
        if worker is not None and worker.poll() is not None:
            raise RuntimeError(f"Worker arrêté prématurément pendant : {label}")
        if monotonic() >= next_update:
            print(f"En cours : {label}", flush=True)
            next_update = monotonic() + 15
        if page is None:
            sleep(0.2)
        else:
            page.wait_for_timeout(200)
    raise TimeoutError(f"Délai dépassé ({timeout}s) : {label}")

def _serve_vision(server, listener):
    """Serve Vision on a selector loop, as it runs on Linux in production.

    Uvicorn picks the Windows Proactor loop by default. When a Chromium
    connection is reset (WinError 10054), CPython 3.13's
    ``_ProactorBasePipeTransport._call_connection_lost`` raises on
    ``socket.shutdown()`` before ``Server._detach()``: the server keeps a
    phantom connection and ``wait_closed()`` — awaited by Uvicorn even under
    ``force_exit`` — never returns. The selector transport only closes its
    socket, so every connection is detached and shutdown completes.
    """

    asyncio.run(server.serve(sockets=[listener]), loop_factory=asyncio.SelectorEventLoop)


def _stop_vision(server, thread):
    """Stop Uvicorn; the selector loop needs no wake-up of a pending accept."""

    server.should_exit = True
    thread.join(timeout=10)
    if thread.is_alive():
        server.force_exit = True
        thread.join(timeout=5)
    if thread.is_alive():
        raise RuntimeError("Vision ne s'est pas arrêté après arrêt forcé")


def _model_settings(args):
    cache = args.katsuyu.resolve() / ".benchmark-cache"
    runtime = args.ai_runtime or cache / "runtime-b10545" / "llama-server.exe"
    model = args.ai_model or cache / "models" / DEFAULT_MODEL
    digest = args.ai_model_sha256 or (DEFAULT_SHA256 if not args.ai_model else None)
    if not runtime.is_file() or not model.is_file():
        raise FileNotFoundError(
            "Moteur/modèle IA absent : préciser --ai-runtime et --ai-model"
        )
    if not digest:
        raise ValueError("Un modèle personnalisé exige --ai-model-sha256")
    if not 2048 <= args.ai_context_size <= 32768:
        raise ValueError("--ai-context-size doit être compris entre 2048 et 32768")
    return runtime.resolve(), model.resolve(), digest


def run(*, args):
    stamp = datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y%m%d-%H%M%S")
    output = args.report_dir.resolve() / f"{stamp}-{uuid4().hex[:8]}"
    output.mkdir(parents=True)
    checks, details = [], {"rapport": str(output / "report.json")}
    report = {
        "started_at": datetime.now(ZoneInfo("Europe/Paris")).isoformat(),
        "checks": checks,
        "details": details,
        "screenshots": [],
    }

    def check(label, passed):
        checks.append((label, bool(passed)))
        print(f"{'✓' if passed else '✗'} {label}", flush=True)
        if not passed:
            raise AssertionError(label)

    try:
        runtime, model, digest = _model_settings(args)
        report["sources"] = {
            "agent": str(args.agent.resolve()),
            "katsuyu": str(args.katsuyu.resolve()),
            "vision": str(args.vision.resolve()),
            "model": str(model),
            "sha256": digest,
        }
        with ExitStack() as stack:
            root = Path(
                stack.enter_context(TemporaryDirectory(prefix="ohana-full-stack-"))
            )
            jobs = DistributedJobRepository(root / "jobs.db")
            stack.callback(jobs.close)
            incidents = TsunadeIncidentRepository(root / "incidents.db")
            stack.callback(incidents.close)
            infrastructure = root / "infrastructure.yaml"
            infrastructure.write_text(
                "infrastructure:\n  id: sandbox\n  name: Ohana Sandbox\n"
                "  environment: development\n"
                "nodes:\n  - id: infra-01\n    name: INFRA-01 Sandbox\n"
                "    endpoint:\n      type: ip\n      address: 127.0.0.1\n"
                "services:\n  - id: dhcp\n    name: DHCP\n    type: dhcp\n"
                "    node: infra-01\n    implementation: dnsmasq\n",
                encoding="utf-8",
            )
            # Only the physical journal source is supplied by the lab. Job-bound
            # authorization, HTTP transport and analysis use production code.
            log_time = datetime.now(ZoneInfo("Europe/Paris")).isoformat()
            journal = (
                f"{log_time} ERROR TemplateError: ValueError: "
                "Template error: float got invalid input 'unavailable' "
                "when rendering template for sensor.pool_temperature\n"
                f"{log_time} ERROR Error rendering template: "
                "sensor.pool_temperature cannot be converted with float "
                "because its state is unavailable\n"
            )

            def read_journal(_start, _end, limit):
                payload = journal.encode("utf-8")
                return payload[-limit:].decode("utf-8", errors="replace"), len(
                    payload
                ) > limit

            service = AdministrationService(
                infrastructure_repository=InfrastructureConfigurationRepository(
                    infrastructure
                ),
                job_repository=jobs,
                incident_repository=incidents,
                # Real dnsmasq executor; its restart request stays in the lab.
                dhcp_repository=DnsmasqDHCPRepository(
                    main_config_path=root / "dnsmasq.conf",
                    reservation_paths={},
                    leases_path=root / "dnsmasq.leases",
                    reload_request_path=root / "run" / "dhcp-reload.request",
                ),
                log_sources=("infra-01",),
                log_timeout_seconds=args.stack_timeout,
                wake_enabled=False,
                wake_shutdown_after_completion=False,
                log_source_broker=LogSourceBroker(BackupConfig(), jobs, read_journal),
                expertise_service=TsunadeExpertiseService(
                    incidents=incidents,
                    investigations=NoProbes(),
                    ai_dispatcher=jobs.create,
                ),
            )
            admin_token, worker_token = (
                secrets.token_urlsafe(32),
                secrets.token_urlsafe(32),
            )
            admin_file, worker_file = root / "admin.token", root / "worker.token"
            admin_file.write_text(admin_token, encoding="utf-8")
            worker_file.write_text(worker_token, encoding="utf-8")
            cert, key = certificate(root)
            admin = ObservedServer(service=service, token=admin_token, port=0)
            admin.start()
            stack.callback(admin.stop)
            worker_api = ObservedServer(
                service=service,
                token=admin_token,
                worker_token=worker_token,
                worker_only=True,
                port=0,
                tls_certificate_file=cert,
                tls_private_key_file=key,
            )
            worker_api.start()
            stack.callback(worker_api.stop)
            admin_url = f"http://127.0.0.1:{admin.address[1]}"
            worker_url = f"https://127.0.0.1:{worker_api.address[1]}"
            app = build_application(
                configuration=ApplicationConfiguration.model_validate(
                    {
                        "name": "Ohana Sandbox",
                        "storage": {"database_path": str(root / "vision.db")},
                        "agent": {
                            "administration_enabled": True,
                            "administration_url": admin_url,
                            "token_file": str(admin_file),
                        },
                    }
                )
            )
            stack.callback(app.state.context.observation_store.close)
            stack.callback(app.state.context.incident_store.close)
            shizune = args.vision.resolve().parent / "Ohana-Shizune" / "Shizune" / "PWA"
            if not shizune.is_dir():
                shizune = root / "shizune-unconfigured"
                shizune.mkdir()
            for route in app.routes:
                if getattr(route, "name", None) == "shizune":
                    route.app = StaticFiles(directory=shizune, html=True)
            listener = socket.socket()
            stack.callback(listener.close)
            listener.bind(("127.0.0.1", 0))
            listener.listen(128)
            vision_url = f"http://127.0.0.1:{listener.getsockname()[1]}"
            server = uvicorn.Server(uvicorn.Config(app, log_level="warning"))
            thread = Thread(target=_serve_vision, args=(server, listener), daemon=True)
            thread.start()
            stack.callback(_stop_vision, server, thread)
            _wait("démarrage Vision", lambda: server.started, timeout=20)

            stop_file = root / "worker.stop"
            config = {
                "checkout": str(args.katsuyu.resolve()),
                "url": worker_url,
                "token_file": str(worker_file),
                "ca": str(cert),
                "status_file": str(root / "worker-status.json"),
                "runtime": str(runtime),
                "model": str(model),
                "sha256": digest,
                "model_id": model.stem.lower(),
                "context_size": args.ai_context_size,
                "stop_file": str(stop_file),
            }
            config_file = root / "worker.json"
            config_file.write_text(json.dumps(config), encoding="utf-8")
            worker_log = stack.enter_context(
                (root / "worker.log").open("w", encoding="utf-8")
            )
            worker = subprocess.Popen(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(Path(__file__).with_name("worker.py")),
                    str(config_file),
                ],
                cwd=root,
                stdout=worker_log,
                stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
            )
            stack.callback(stop_worker, worker, stop_file)
            _wait(
                "enregistrement Katsuyu HTTPS",
                lambda: any(
                    path == "/v1/jobs/workers/register" and code == 200
                    for _, path, code in worker_api.responses
                ),
                timeout=20,
                worker=worker,
            )
            check("Worker enregistré par HTTPS avec certificat local vérifié", True)

            playwright = stack.enter_context(sync_playwright())
            browser = playwright.chromium.launch()
            stack.callback(browser.close)
            context = browser.new_context(viewport={"width": 1440, "height": 1000})
            page = context.new_page()
            errors, failed_responses = [], []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on(
                "response",
                lambda response: (
                    failed_responses.append(
                        {"url": response.url, "status": response.status}
                    )
                    if response.status >= 500
                    else None
                ),
            )
            page.goto(vision_url + "/ui/", wait_until="networkidle")
            page.locator('[data-navigation-target="incidents"]').click()
            expect(page.locator("#incidents-heading")).to_be_visible()
            expect(page.locator("#tsunade-log-check")).to_be_enabled(timeout=15000)
            with page.expect_response(
                lambda response: (
                    response.url.endswith("/tsunade/incidents/logs/check")
                    and response.request.method == "POST"
                )
            ) as response_info:
                page.locator("#tsunade-log-check").click()
            check("Contrôle des journaux demandé depuis Vision", response_info.value.ok)
            log_job = _wait(
                "contrôle des journaux réseau",
                lambda: (
                    job
                    if (job := jobs.latest_for_incident("logs.health_check", None))
                    and job.status.value in {"SUCCEEDED", "FAILED", "TIMEOUT"}
                    else None
                ),
                timeout=60,
                worker=worker,
                page=page,
            )
            check(
                "Collecte autorisée et analyse Katsuyu terminées",
                log_job.status.value == "SUCCEEDED",
            )
            report["logs_job_id"] = str(log_job.job_id)
            _wait("incident Tsunade", lambda: incidents.list(), timeout=15, page=page)
            incident = incidents.list()[0]
            incident_id = str(incident.incident_id)
            expect(page.locator("#incidents-list .incident-card")).to_have_count(
                1, timeout=15000
            )
            page.screenshot(path=str(output / "vision-before-ai.png"), full_page=True)
            report["screenshots"].append("vision-before-ai.png")
            incident = incidents.get(incident.incident_id)

            automatic_escalations = [
                event
                for event in incident.events
                if event.kind == "diagnostic"
                and event.payload.get("cycle_status") == "ai_queued"
                and event.payload.get("trigger") == "automatic_escalation"
            ]

            check(
                "Tsunade a automatiquement demandé Katsuyu sur l'incident ambigu",
                len(automatic_escalations) == 1,
            )
            ai_job = _wait(
                "inférence IA locale réelle",
                lambda: (
                    job
                    if (job := jobs.latest_for_incident("ai.inference", incident_id))
                    and job.status.value in {"SUCCEEDED", "FAILED", "TIMEOUT"}
                    else None
                ),
                timeout=args.stack_timeout,
                worker=worker,
                page=page,
            )
            report["ai_job"] = ai_job.model_dump(mode="json")
            check(
                "Inférence réelle terminée et résultat accepté",
                ai_job.status.value == "SUCCEEDED",
            )
            check(
                "Modèle vérifié et tokens générés",
                ai_job.result["model_sha256"] == digest
                and ai_job.result["metrics"]["completion_tokens"] > 0,
            )
            _wait(
                "traitement Tsunade",
                lambda: not jobs.pending_completions(),
                timeout=20,
                worker=worker,
                page=page,
            )
            diagnosed = incidents.get(incident.incident_id)
            assessment = incident_assessment(diagnosed)

            ai_diagnostics = [
                event
                for event in diagnosed.events
                if event.kind == "diagnostic"
                and event.payload.get("cycle_status") == "ai_completed"
            ]

            check(
                "Le vrai Katsuyu classe l'anomalie comme KO",
                ai_job.result.get("verdict") == "KO",
            )

            check(
                "Le vrai Katsuyu produit au moins une hypothèse",
                bool(ai_job.result.get("hypotheses")),
            )

            check(
                "Le vrai Katsuyu indique le contexte restant à vérifier",
                bool(ai_job.result.get("missing_context")),
            )

            check(
                "Tsunade conserve le résultat Katsuyu comme hypothèse PROBABLE",
                (
                    len(ai_diagnostics) == 1
                    and ai_diagnostics[0].payload.get("epistemic_status") == "hypothesis"
                    and ai_diagnostics[0].payload.get("diagnostic_level") == "PROBABLE"
                    and assessment["diagnostic_level"] == "PROBABLE"
                ),
            )

            check(
                "L'hypothèse Katsuyu demande une investigation sans autoriser d'action",
                (
                    assessment["decision"] == "investigate"
                    and assessment["decision"] != "action_required"
                ),
            )

            actions = [
                event
                for event in diagnosed.events
                if event.kind == "action"
                and event.payload.get("origin") == "katsuyu_ai"
            ]

            investigation_commands = (
                actions[-1].payload.get("investigation_commands", [])
                if actions
                else []
            )

            check(
                "Katsuyu conduit à une vérification concrète en lecture seule",
                any(
                    command.get("safety") == "Lecture seule"
                    and "sensor.pool_temperature" in command.get("command", "")
                    for command in investigation_commands
                ),
            )
            page.reload(wait_until="networkidle")
            page.locator('[data-navigation-target="incidents"]').click()
            expect(page.locator("#incidents-error")).not_to_be_visible()
            page.locator(f'[data-tsunade-details="{incident_id}"]').click()
            katsuyu_analysis = page.locator(
                "#incidents-list .incident-katsuyu-analysis"
            )

            expect(katsuyu_analysis).to_have_count(
                1,
                timeout=15000,
            )

            expect(katsuyu_analysis).to_contain_text(
                "Analyse Katsuyu"
            )

            expect(katsuyu_analysis).to_contain_text(
                "Hypothèses exploitables"
            )

            expect(page.locator("#incidents-list")).to_contain_text(
                "À approfondir"
            )

            check(
                "Analyse Katsuyu effectivement rendue dans le dossier Vision",
                True,
            )
            check("Résumé IA effectivement rendu dans le dossier Vision", True)

            # Phase 2: supervised repair decisions clicked in the real Vision.
            reload_request = root / "run" / "dhcp-reload.request"
            repairs = TsunadeExpertiseService(
                incidents=incidents, investigations=DnsmasqStopped()
            )
            repairs.set_repair_proposer(
                lambda repair_incident_id: service.propose_incident_repair(
                    str(repair_incident_id), {}, automatic=True
                )
            )

            def dnsmasq(status):
                return incidents.process(
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

            def proposal():
                repair_incident = dnsmasq(ObservationStatus.UNHEALTHY)
                repairs.diagnose(repair_incident.incident_id)
                proposed = incidents.get(repair_incident.incident_id).repairs[0]
                page.reload(wait_until="networkidle")
                page.locator('[data-navigation-target="incidents"]').click()
                return repair_incident.incident_id, str(proposed.repair_id)

            def post(fragment, locator):
                with page.expect_response(
                    lambda response: response.url.endswith(fragment)
                    and response.request.method == "POST"
                ) as response_info:
                    locator.click()
                return response_info.value.ok

            repair_incident_id, repair_id = proposal()
            defer = page.locator(
                f'[data-tsunade-repair-decision="defer"][data-repair-id="{repair_id}"]'
            )
            expect(defer).to_be_visible(timeout=15000)
            deferred_ok = post("/repairs/defer", defer)
            expect(page.locator("#incidents-list")).to_contain_text(
                "reportée jusqu’à", timeout=15000
            )
            check(
                "Réparation reportée depuis Vision, sans exécution",
                deferred_ok
                and incidents.get(repair_incident_id).repairs[0].deferred_until
                is not None
                and not reload_request.exists(),
            )
            authorized_ok = post(
                "/repairs/authorize",
                page.locator(f'[data-tsunade-repair-authorize="{repair_id}"]'),
            )
            expect(page.locator("#incidents-list")).to_contain_text(
                "Exécutée, vérification Shikamaru en attente", timeout=15000
            )
            check(
                "Réparation autorisée depuis Vision : dnsmasq demandé une fois",
                authorized_ok
                and reload_request.exists()
                and incidents.get(repair_incident_id).repairs[0].status
                == "verifying",
            )
            dnsmasq(ObservationStatus.HEALTHY)
            check(
                "Shikamaru vérifie la réparation autorisée depuis Vision",
                incidents.get(repair_incident_id).repairs[0].status == "succeeded",
            )
            reload_request.unlink()  # The helper consumes each request.
            refused_incident_id, refused_id = proposal()
            page.once("dialog", lambda dialog: dialog.accept())
            refused_ok = post(
                "/repairs/refuse",
                page.locator(
                    f'[data-tsunade-repair-decision="refuse"]'
                    f'[data-repair-id="{refused_id}"]'
                ),
            )
            expect(page.locator("#incidents-list")).to_contain_text(
                "Refusée, aucune action exécutée", timeout=15000
            )
            check(
                "Réparation refusée depuis Vision après confirmation, sans exécution",
                refused_ok
                and incidents.get(refused_incident_id).repairs[0].status == "refused"
                and not reload_request.exists(),
            )
            page.screenshot(path=str(output / "vision-repairs.png"), full_page=True)
            report["screenshots"].append("vision-repairs.png")
            for name, width, height in (("desktop", 1440, 1000), ("mobile", 390, 844)):
                page.set_viewport_size({"width": width, "height": height})
                expect(page.locator("#incidents-heading")).to_be_visible()
                check(
                    f"Vision {name} sans débordement horizontal",
                    page.evaluate(
                        "document.documentElement.scrollWidth <= window.innerWidth + 1"
                    ),
                )
                filename = f"vision-{name}.png"
                page.screenshot(path=str(output / filename), full_page=True)
                report["screenshots"].append(filename)
            report["browser_errors"] = errors
            report["failed_responses"] = failed_responses
            check(
                "Aucune erreur JavaScript ou HTTP serveur dans Vision",
                not errors and not failed_responses,
            )
            check(
                "Cycle réseau : register, next, source, heartbeat, complete",
                all(
                    any(
                        fragment in path and code == 200
                        for _, path, code in worker_api.responses
                    )
                    for fragment in (
                        "/register",
                        "/next",
                        "/log-source/",
                        "/heartbeat",
                        "/complete",
                    )
                ),
            )
            report["worker_http"] = [
                {"method": method, "path": path, "status": code, "count": count}
                for (method, path, code), count in worker_api.responses.items()
            ]
            report["incident"] = service.read_incident(incident_id)
            details["IA"] = (
                f"{model.name} ; "
                f"{ai_job.result['metrics']['completion_tokens']} tokens générés"
            )
            details["Vision"] = (
                "Desktop et mobile, actions et résultat IA vérifiés dans Chromium"
            )
    except Exception as exc:
        checks.append((f"{type(exc).__name__}: {exc}", False))
        report["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        report["passed"] = bool(checks) and all(passed for _, passed in checks)
        report["finished_at"] = datetime.now(ZoneInfo("Europe/Paris")).isoformat()
        (output / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
    return {"passed": report["passed"], "checks": checks, "details": details}
