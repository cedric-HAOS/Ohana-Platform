"""Daily ZWAVE-01 log review through the Home Assistant Supervisor.

Production: every daily check of ZWAVE-01 was reported truncated since 20
September. Katsuyu kept the newest 10 000 lines of each Supervisor log, and
ZWAVE-01 logs more than that in 24 hours: the window was never covered, the
incident could not resolve and disappeared anomalies were never recognised.
The byte budget (2 MB) was far from reached.

The fake Supervisor below honours the ``lines`` parameter the way the real
one does: it returns the newest lines of 30 000 spread over 25 hours.
"""

from __future__ import annotations

import threading
from datetime import UTC, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from ohana_agent.api.service import AdministrationService
from ohana_agent.infrastructure.repository import InfrastructureConfigurationRepository
from ohana_katsuyu.handlers import HandlerContext, LogsHealthCheckHandler

from scenarios._support import environment

WORKER = "sandbox-worker"
LINES = 30_000


def _core_log(now) -> list[bytes]:
    """25 hours of chatty INFO lines, one error before and one inside the window."""
    utc_now = now.astimezone(UTC)
    start = utc_now - timedelta(hours=25)
    step = timedelta(hours=25) / LINES
    lines = [
        (start + step * index).isoformat().encode() + b" INFO Z-Wave value updated\n"
        for index in range(LINES)
    ]
    lines.insert(
        10,
        (start + step * 10).isoformat().encode()
        + b" ERROR Node 12 transmission failed yesterday\n",
    )
    lines.append(
        (utc_now - timedelta(minutes=5)).isoformat().encode()
        + b" ERROR Node 17 transmission failed\n"
    )
    return lines


def _serve(lines: list[bytes], requested: list[int]):
    class Supervisor(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - http.server API
            url = urlparse(self.path)
            if url.path != "/api/hassio/core/logs/latest":
                self.send_error(404)
                return
            count = int(parse_qs(url.query).get("lines", ["100"])[0])
            requested.append(count)
            body = b"".join(lines[-count:])
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args) -> None:
            return None

    server = ThreadingHTTPServer(("127.0.0.1", 0), Supervisor)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def run() -> dict:
    checks = []
    details = {}
    with environment() as s:
        s.service = AdministrationService(
            infrastructure_repository=InfrastructureConfigurationRepository(
                s.root / "infra.yaml"
            ),
            job_repository=s.jobs,
            incident_repository=s.incidents,
            expertise_service=s.expertise,
            log_sources=("zwave-01",),
        )
        s.jobs.register_worker(
            {
                "worker_id": WORKER,
                "platform": "Sandbox",
                "worker_version": "dev",
                "capabilities": ["logs.health_check"],
            }
        )
        requested: list[int] = []
        server = _serve(_core_log(s.clock()), requested)
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            s.service.request_log_health_check(
                now=s.clock(), max_bytes=2 * 1024 * 1024, window_hours=24
            )
            claimed = s.service.next_worker_job(
                {"worker_id": WORKER, "supported_types": ["logs.health_check"]}
            ).job
            assert claimed is not None and claimed.type == "logs.health_check"

            def source_provider(job_id, worker_id, attempt, source):
                return {
                    "source": source,
                    "base_url": base_url,
                    "url": f"{base_url}/api/hassio/core/logs/latest?lines=10000",
                    "access_token": "sandbox-token",
                    "verify_tls": True,
                    "timeout_seconds": 10,
                    "addon_name_patterns": [],
                }

            result = LogsHealthCheckHandler(source_provider).execute(
                claimed.parameters,
                HandlerContext(job_id=str(claimed.job_id), worker_id=WORKER, attempt=1),
            )
        finally:
            server.shutdown()
            server.server_close()
        [zwave] = result["sources"]
        signatures = [finding["signature"] for finding in zwave["findings"]]
        details["lignes demandées au Supervisor"] = ", ".join(map(str, requested))
        details["octets retenus"] = zwave["fetched_bytes"]
        details["lignes analysées"] = zwave["analyzed_lines"]
        checks += [
            (
                "plus de 10 000 lignes en 24 h : la fenêtre est couverte, collecte "
                "non tronquée",
                zwave["truncated"] is False,
            ),
            (
                "seules les lignes de la fenêtre comptent dans le budget d'octets",
                zwave["fetched_bytes"] < 2 * 1024 * 1024
                and zwave["analyzed_lines"] >= LINES * 24 // 25,
            ),
            (
                "l'erreur de la fenêtre est retenue, celle de la veille non",
                any(item.endswith("transmission failed") for item in signatures)
                and not any("yesterday" in item for item in signatures),
            ),
        ]
    details["portée"] = (
        "Agent et analyseur Katsuyu locaux, faux Supervisor HTTP ; aucun accès "
        "production"
    )
    details["limites"] = "Journal Core synthétique ; add-ons (WebSocket) non simulés"
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
