"""Extension to 24 hours of a finished log follow-up, from the Vision button.

Real Agent HTTP listener and service, real Vision server (uvicorn, SQLite) and
Chromium clicking the real button, real Katsuyu ``LogsInvestigateHandler``
filtering a lab journal by the window Agent sent. The AI payloads are
recorded-contract fixtures and the journal is synthetic; nothing on Konoha is
touched.
"""

from __future__ import annotations

import json
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

from ohana_agent.api.http import AdministrationHTTPServer
from ohana_agent.tsunade.incident_summary import incident_assessment
from ohana_agent.tsunade.local_time import paris_now
from ohana_katsuyu.handlers import HandlerContext, LogsInvestigateHandler
from ohana_katsuyu.models import LogsInvestigateParameters as KatsuyuParameters
from playwright.sync_api import sync_playwright

from scenarios._support import (
    ai_result,
    authorize,
    environment,
    job_counts,
    poll,
    propose,
    restart,
)
from scenarios.katsuyu_shizune_vitals import ADMIN_TOKEN
from scenarios.ohana_self_supervision import _http, _serve_vision

BUTTON = "[data-tsunade-log-extend]"


def _journal(now: datetime) -> str:
    """One timeout per age: inside both windows, only the 24 h one, outside both."""
    ages = (timedelta(minutes=90), timedelta(hours=3), timedelta(hours=23))
    ages += (timedelta(hours=25),)
    return "\n".join(
        f"{(now - age).isoformat()} ERROR Connection timeout" for age in ages
    )


def _collect(s, job, content: str) -> dict:
    """Run Katsuyu's own handler on the job exactly as Agent built it."""

    def source_provider(job_id, worker_id, attempt, source):
        assert (job_id, worker_id, attempt, source) == (
            str(job.job_id),
            "sandbox-worker",
            job.attempt,
            "ha-01",
        )
        return {"source": source, "transport": "inline", "content": content}

    result = LogsInvestigateHandler(source_provider).execute(
        job.parameters,
        HandlerContext(
            job_id=str(job.job_id), worker_id="sandbox-worker", attempt=job.attempt
        ),
    )
    completion = {
        "worker_id": "sandbox-worker",
        "attempt": job.attempt,
        "status": "SUCCEEDED",
        "result": result,
    }
    s.service.complete_job(str(job.job_id), completion)
    return result


def _review(s):
    review = poll(s)
    assert review is not None and review.type == "ai.inference"
    s.service.complete_job(
        str(review.job_id),
        {
            "worker_id": "sandbox-worker",
            "attempt": review.attempt,
            "status": "SUCCEEDED",
            "result": ai_result(),
        },
    )
    return review


def _window(job) -> timedelta:
    return datetime.fromisoformat(
        job.parameters["window_ended_at"]
    ) - datetime.fromisoformat(job.parameters["window_started_at"])


def run() -> dict:
    checks: list[tuple[str, bool]] = []
    details: dict[str, str] = {}
    output = (
        Path(__file__).resolve().parents[1]
        / "runs"
        / (paris_now().strftime("%Y%m%d-%H%M%S") + "-log-window-extension")
    )
    output.mkdir(parents=True)
    with environment() as s:
        content = _journal(s.clock())

        # A first cycle, as in production: 2 hours, then nothing more to offer.
        propose(s)
        authorize(s)
        first = poll(s)
        assert first is not None and first.type == "logs.investigate"
        first_result = _collect(s, first, content)
        _review(s)
        incident = s.incidents.get(s.incident.incident_id)
        before = incident_assessment(incident)
        checks.extend(
            [
                ("première collecte limitée à deux heures", _window(first) == timedelta(hours=2)),
                (
                    "première collecte : seule la ligne de 90 minutes correspond",
                    first_result["matched_lines"] == 1,
                ),
                (
                    "investigation terminée, extension proposée",
                    before["state"] == "investigation_exhausted"
                    and before["followup"]["window_extension_available"] is True
                    and before["followup"]["window_hours"] == 2,
                ),
                (
                    "aucune demande en attente dans Shizune",
                    not s.service.read_companion_requests().requests,
                ),
            ]
        )

        administration = AdministrationHTTPServer(
            service=s.service, token=ADMIN_TOKEN, worker_token="w" * 32, port=0
        )
        administration.start()
        address, port = administration.address
        context, server, thread, listener, base = _serve_vision(
            output, f"http://{address}:{port}", f"http://{address}:{port}"
        )
        try:
            listed, _ = _http(base, "/api/administration/tsunade/incidents?state=active")
            projected = listed["incidents"][0]["assessment"]["followup"]
            checks.append(
                (
                    "Vision reçoit l'extension proposée par Agent",
                    projected["window_extension_available"] is True,
                )
            )
            errors: list[str] = []
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                page = browser.new_page(viewport={"width": 1440, "height": 1000})
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(base + "/ui/#incidents")
                page.wait_for_selector(BUTTON, timeout=15000)
                label = page.locator(BUTTON).inner_text()
                page.screenshot(path=str(output / "log-window-extension-before.png"))
                page.locator(BUTTON).click()
                page.wait_for_selector(BUTTON, state="detached", timeout=15000)
                banner = page.locator("#incidents-error").inner_text()
                page.screenshot(path=str(output / "log-window-extension-after.png"))
                checks.extend(
                    [
                        ("bouton nommé avec la fenêtre de 24 h", "24 h" in label),
                        ("clic : aucune erreur affichée", banner.strip() == ""),
                    ]
                )
                second = poll(s)
                assert second is not None and second.type == "logs.investigate"
                after_click = incident_assessment(
                    s.incidents.get(s.incident.incident_id)
                )
                request = s.incidents.get_user_request(
                    s.incidents.get(s.incident.incident_id).followup["request_id"]
                )
                checks.extend(
                    [
                        (
                            "autorisation tracée comme venant de Vision",
                            request.answer == "AUTHORIZE"
                            and request.answer_source == "vision",
                        ),
                        (
                            "collecte de 24 heures, même motif, mêmes limites",
                            _window(second) == timedelta(hours=24)
                            and second.parameters["pattern"] == first.parameters["pattern"]
                            and second.parameters["max_bytes"]
                            == first.parameters["max_bytes"]
                            and second.parameters["source"] == "ha-01",
                        ),
                        (
                            "pendant la collecte : plus d'extension offerte",
                            after_click["state"] == "analyzing"
                            and after_click["followup"]["window_extension_available"]
                            is False,
                        ),
                        (
                            "le contrat de Katsuyu accepte la fenêtre de 24 heures",
                            KatsuyuParameters.model_validate(second.parameters)
                            is not None,
                        ),
                    ]
                )

                result = _collect(s, second, content)
                review = _review(s)
                evidence = {
                    item["source"]: json.loads(item["content"])
                    for item in review.parameters["evidence"]
                }
                done = incident_assessment(s.incidents.get(s.incident.incident_id))
                checks.extend(
                    [
                        (
                            "Katsuyu : lignes des 24 h seulement (90 min, 3 h, 23 h)",
                            result["matched_lines"] == 3,
                        ),
                        (
                            "la réévaluation voit la fenêtre de 24 heures",
                            evidence["investigation.followup"]["scope"][
                                "window_started_at"
                            ]
                            == second.parameters["window_started_at"],
                        ),
                        (
                            "cycle terminé, extension non reproposée",
                            done["state"] == "investigation_exhausted"
                            and done["followup"]["window_hours"] == 24
                            and done["followup"]["window_extension_available"] is False,
                        ),
                    ]
                )

                page.locator("#refresh-button").click()
                page.wait_for_timeout(1500)
                checks.append(
                    ("Vision : plus de bouton après la collecte de 24 h", page.locator(BUTTON).count() == 0)
                )
                checks.append(("Chromium : aucune erreur de page", not errors))
                browser.close()

            try:
                _http(
                    base,
                    "/api/administration/tsunade/incidents/"
                    f"{s.incident.incident_id}/logs/investigate/extend",
                    {"source": "vision", "authorized_by": "utilisateur Vision"},
                )
                refused = False
            except urllib.error.HTTPError as error:
                refused = 400 <= error.code < 500
            checks.extend(
                [
                    ("seconde extension refusée par Agent via Vision", refused),
                    (
                        "aucune seconde collecte de 24 heures",
                        job_counts(s)["logs.investigate"] == 2,
                    ),
                ]
            )
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            listener.close()
            administration.stop()
            context.observation_store.close()
            context.incident_store.close()

        persisted = incident_assessment(s.incidents.get(s.incident.incident_id))
        restart(s)
        restored = incident_assessment(s.incidents.get(s.incident.incident_id))
        checks.extend(
            [
                ("état identique après reprise depuis SQLite", restored == persisted),
                ("aucun travail relancé après reprise", poll(s) is None),
                (
                    "cycle borné : trois IA enregistrées, deux collectes",
                    job_counts(s) == {"ai.inference": 3, "logs.investigate": 2},
                ),
            ]
        )
        details["portée"] = (
            "Agent, Vision, Chromium et handler Katsuyu locaux ; IA enregistrée ; "
            "journal synthétique ; aucun accès production"
        )
        details["captures"] = str(output)
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
