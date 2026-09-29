"""Phase 6, lot 3: interrupted jobs and an AI runtime that cannot answer.

Part A: an AI job whose worker stops every time (PC off, crash) is resumed
twice, then fails explicitly, and Tsunade records a bounded fallback with no
AI-derived conclusion. Part B: a real Katsuyu worker over HTTP resumes a job
after its predecessor vanished mid-job, keeps running deterministic jobs
without the AI runtime, and an AI job it cannot run fails with its cause.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from pathlib import Path
from uuid import uuid4

import ohana_katsuyu
from ohana_agent.api.http import AdministrationHTTPServer
from ohana_katsuyu.ai import AiInferenceHandler
from ohana_katsuyu.handlers import KatsuyuWorkspace, SystemHealthHandler
from ohana_katsuyu.worker import AgentClient, KatsuyuWorker

from scenarios._support import environment, poll

ADMIN_TOKEN = "tsunade-sandbox"
WORKER_TOKEN = "katsuyu-sandbox-secret"
REAL_WORKER = "katsuyu-resilience"


def _ai_job(s, timeout: int = 6 * 3600):
    return s.jobs.create(
        {
            "job_id": str(uuid4()),
            "created_at": s.clock().isoformat(),
            "type": "ai.inference",
            "timeout": timeout,
            "parameters": {
                "incident_id": str(s.incident.incident_id),
                "question": "Pourquoi ?",
                "evidence": [{"source": "shikamaru.observation", "content": "{}"}],
            },
        }
    )


def _ai_diagnostics(s) -> list:
    return [
        event
        for event in s.incidents.get(s.incident.incident_id).events
        if event.kind == "diagnostic"
        and event.payload.get("origin") == "katsuyu_ai"
    ]


def run() -> dict:
    checks: list[tuple[str, bool]] = []
    details: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Part A: interrupted every time -> explicit failure, no conclusion
    # ------------------------------------------------------------------
    with environment() as s:
        job = _ai_job(s)
        for _ in range(3):
            claimed = poll(s)
            assert claimed is not None and claimed.job_id == job.job_id
            s.clock.advance(seconds=61)  # the PC vanished, no more heartbeat
        assert poll(s) is None  # recovery, then Tsunade processes the failure
        failed = s.jobs.get(str(job.job_id))
        diagnostics = _ai_diagnostics(s)
        payload = diagnostics[0].payload if diagnostics else {}
        checks += [
            (
                "job IA interrompu trois fois : échec explicite, plus de reprise",
                failed.status.value == "FAILED"
                and failed.attempt == 3
                and failed.error is not None
                and failed.error.code == "worker.interrupted",
            ),
            (
                "aucun nouveau job IA créé après l'abandon",
                s.jobs.count("ai.inference") == 1,
            ),
            (
                "Tsunade consigne l'échec sans conclusion IA (statut épistémique « none »)",
                len(diagnostics) == 1
                and payload.get("cycle_status") == "ai_failed"
                and payload.get("epistemic_status") == "none"
                and payload.get("diagnostic_level") == "INSUFFICIENT_CONTEXT",
            ),
            (
                "décision de repli : surveiller, aucune action corrective autorisée",
                payload.get("decision") == "watch"
                and payload.get("decision_source") == "fallback"
                and "Aucun élément ne permet d’autoriser une action corrective"
                in payload.get("conclusion", ""),
            ),
            (
                "la cause de l'interruption est conservée pour Vision",
                "arrêté 3 fois" in payload.get("error", ""),
            ),
            (
                "l'incident reste actif, aucune réparation proposée",
                s.incidents.get(s.incident.incident_id).state == "active"
                and not s.service.read_companion_requests().requests,
            ),
        ]
        details["échec explicite"] = failed.error.message if failed.error else ""

        # --------------------------------------------------------------
        # Part B: real Katsuyu worker over HTTP, no AI runtime
        # --------------------------------------------------------------
        with tempfile.TemporaryDirectory(prefix="ohana-sandbox-resilience-") as tmp:
            root = Path(tmp)
            server = AdministrationHTTPServer(
                service=s.service,
                token=ADMIN_TOKEN,
                worker_token=WORKER_TOKEN,
                port=0,
            )
            server.start()
            try:
                host, port = server.address
                workspace = KatsuyuWorkspace(root / "workspace")
                handlers = {
                    "system.health": SystemHealthHandler(workspace),
                    "ai.inference": AiInferenceHandler(
                        runtime=root / "llama-server.exe",
                        model=root / "model.gguf",
                        model_id="ministral-sandbox",
                        model_sha256="a" * 64,
                    ),
                }

                def new_worker() -> KatsuyuWorker:
                    return KatsuyuWorker(
                        client=AgentClient(f"http://{host}:{port}", WORKER_TOKEN),
                        worker_id=REAL_WORKER,
                        handlers=handlers,
                        heartbeat_seconds=0.2,
                        runtime_refresh_seconds=0,
                    )

                health_id = str(uuid4())
                s.jobs.create(
                    {
                        "protocol_version": 1,
                        "job_id": health_id,
                        "type": "system.health",
                        "created_at": s.clock().isoformat(),
                        "parameters": {},
                        "timeout": 3600,
                    }
                )
                # A real Katsuyu process claims the job, then is killed like a
                # PC losing power: no completion, no more heartbeat.
                child = subprocess.Popen(  # noqa: S603
                    [
                        sys.executable,
                        str(Path(__file__).with_name("_slow_worker.py")),
                        f"http://{host}:{port}",
                        WORKER_TOKEN,
                        REAL_WORKER,
                        str(root / "child-workspace"),
                        str(Path(ohana_katsuyu.__file__).resolve().parents[1]),
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                deadline = time.monotonic() + 60
                while (
                    s.jobs.get(health_id).status.value != "RUNNING"
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.2)
                was_running = s.jobs.get(health_id).status.value == "RUNNING"
                child.kill()
                child.wait(timeout=10)
                s.clock.advance(seconds=61)

                survivor = new_worker()
                survivor.register()
                resumed = survivor.run_once()
                health = s.jobs.get(health_id)
                checks += [
                    (
                        "processus Katsuyu réel tué en plein job : repris à la tentative 2",
                        was_running
                        and child.returncode not in (None, 0)
                        and resumed
                        and health.status.value == "SUCCEEDED"
                        and health.attempt == 2,
                    ),
                ]

                # Deterministic work keeps running without the AI runtime.
                s.jobs.create(
                    {
                        "protocol_version": 1,
                        "job_id": str(uuid4()),
                        "type": "system.health",
                        "created_at": s.clock().isoformat(),
                        "parameters": {},
                        "timeout": 3600,
                    }
                )
                deterministic = survivor.run_once()
                runtimes = s.jobs.list_workers().workers
                runtime = next(
                    (
                        item.runtimes.get("ai.inference")
                        for item in runtimes
                        if item.worker_id == REAL_WORKER
                    ),
                    None,
                )
                checks += [
                    (
                        "runtime IA absent déclaré, cause lisible",
                        runtime is not None
                        and runtime.state.value == "missing"
                        and "absent" in runtime.detail,
                    ),
                    (
                        "traitement déterministe exécuté malgré l'absence du runtime IA",
                        deterministic,
                    ),
                ]

                # An AI job this PC cannot run fails with its cause.
                ai_job = _ai_job(s, timeout=900)
                ran = survivor.run_once()
                survivor.run_once()  # idle: Tsunade processes the failure
                after = s.jobs.get(str(ai_job.job_id))
                failures = [
                    event
                    for event in _ai_diagnostics(s)
                    if event.payload.get("job_id") == str(ai_job.job_id)
                ]
                checks += [
                    (
                        "job IA impossible : échec explicite avec la cause locale",
                        ran
                        and after.status.value == "FAILED"
                        and after.error is not None
                        and "is missing" in after.error.message,
                    ),
                    (
                        "aucune conclusion artificielle : repli sans statut épistémique",
                        len(failures) == 1
                        and failures[0].payload.get("epistemic_status") == "none"
                        and failures[0].payload.get("cycle_status") == "ai_failed",
                    ),
                ]
                details["runtime IA"] = f"{runtime.state.value} ({runtime.detail})"
                details["échec IA"] = after.error.message if after.error else ""
            finally:
                server.stop()

    details["portée"] = (
        "Agent HTTP, worker Katsuyu et handlers réels ; runtime IA absent sur "
        "disque, disparition du worker simulée par l'avance de l'horloge de l'Agent"
    )
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
