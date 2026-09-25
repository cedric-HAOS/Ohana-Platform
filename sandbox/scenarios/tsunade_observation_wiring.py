from __future__ import annotations

import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch
from uuid import uuid4

import ohana_agent

from ohana_agent.api.service import AdministrationService
from ohana_agent.core.events import EventBus
from ohana_agent.runtime.administration_bootstrap import TsunadeObservationHandler
from ohana_agent.runtime.bootstrap import build_production_agent
from ohana_agent.tsunade.expertise import TsunadeExpertiseService
from ohana_agent.tsunade.incidents import TsunadeIncidentRepository


class FakeVisionClient:
    """Discard Vision exports during the wiring scenario."""

    def send_observation(self, payload: dict[str, Any]) -> None:
        del payload

    def send_infrastructure(self, payload: dict[str, Any]) -> None:
        del payload


def run() -> dict:
    agent_root = Path(ohana_agent.__file__).resolve().parents[2]

    with tempfile.TemporaryDirectory(
        prefix="ohana-sandbox-tsunade-wiring-"
    ) as temporary:
        root = Path(temporary)

        management_token = root / "management.token"
        worker_token = root / "katsuyu.token"
        jobs_database = root / "distributed-jobs.db"

        management_token.write_text(
            "management-secret\n",
            encoding="utf-8",
        )
        worker_token.write_text(
            "worker-secret\n",
            encoding="utf-8",
        )

        application_path = root / "shikamaru.yaml"
        application_path.write_text(
            f"""\
version: 1

agent:
  name: Shikamaru
  environment: test

vision:
  enabled: true
  observation_url: http://127.0.0.1:8000/api/observations
  infrastructure_url: http://127.0.0.1:8000/api/infrastructure

administration:
  enabled: true
  token_file: {management_token.as_posix()}

  jobs:
    enabled: true
    database_path: {jobs_database.as_posix()}
    worker_token_file: {worker_token.as_posix()}

    logs:
      enabled: true
      sources:
        - infra-01

  dhcp:
    enabled: false
""",
            encoding="utf-8",
        )

        incident_id = uuid4()
        log_incident_id = uuid4()

        first_occurrence = SimpleNamespace(
            incident_id=incident_id,
            state="active",
            severity="degraded",
            occurrence_count=1,
            node_id="she-04",
        )

        repeated_occurrence = SimpleNamespace(
            incident_id=incident_id,
            state="active",
            severity="degraded",
            occurrence_count=2,
            node_id="she-04",
            # A real incident always carries its latest decision (Agent 1.31
            # reads it to resume an escalation after an upstream resolution).
            latest_decision=None,
        )

        log_source_occurrence = SimpleNamespace(
            incident_id=log_incident_id,
            state="active",
            severity="degraded",
            occurrence_count=1,
            node_id="infra-01",
        )

        incidents = iter(
            [
                first_occurrence,
                repeated_occurrence,
                log_source_occurrence,
            ]
        )

        captured_handlers: dict[str, Callable[[Any], None]] = {}
        expertise_started: list[str] = []
        created_jobs: list[dict[str, Any]] = []

        original_subscribe = EventBus.subscribe

        def capture_subscribe(
            self: EventBus,
            event_type: type[Any],
            handler: Callable[[Any], None],
        ) -> None:
            if isinstance(handler, TsunadeObservationHandler):
                captured_handlers["tsunade"] = handler

            original_subscribe(
                self,
                event_type,
                handler,
            )

        def fake_process(
            self: TsunadeIncidentRepository,
            observation: object,
        ) -> SimpleNamespace:
            del self, observation
            return next(incidents)

        def fake_start(
            self: TsunadeExpertiseService,
            current_incident_id: object,
            *,
            log_result: dict[str, Any] | None = None,
        ) -> None:
            del self, log_result
            expertise_started.append(
                str(current_incident_id)
            )

        def fake_create_job(
            self: AdministrationService,
            payload: dict[str, Any],
        ) -> dict[str, Any]:
            del self
            created_jobs.append(payload)
            return payload

        previous_directory = Path.cwd()
        service: AdministrationService | None = None

        try:
            os.chdir(agent_root)

            with (
                patch.object(
                    EventBus,
                    "subscribe",
                    new=capture_subscribe,
                ),
                patch.object(
                    TsunadeIncidentRepository,
                    "process",
                    new=fake_process,
                ),
                patch.object(
                    TsunadeExpertiseService,
                    "start",
                    new=fake_start,
                ),
                patch.object(
                    AdministrationService,
                    "create_job",
                    new=fake_create_job,
                ),
            ):
                agent = build_production_agent(
                    application_config_path=application_path,
                    vision_client=FakeVisionClient(),
                )

                assert agent.administration_runtime is not None

                service = agent.administration_runtime.service

                handler = captured_handlers.get("tsunade")

                if handler is None:
                    raise AssertionError(
                        "Le handler Tsunade des observations "
                        "n'a pas été câblé."
                    )

                # 1. Première observation fautive SHE-04 :
                #    Tsunade doit partir directement.
                handler(
                    SimpleNamespace(
                        observation=object(),
                    )
                )

                expertise_after_first = list(
                    expertise_started
                )
                jobs_after_first = list(created_jobs)

                # 2. Même incident, occurrence suivante :
                #    aucune nouvelle expertise.
                handler(
                    SimpleNamespace(
                        observation=object(),
                    )
                )

                expertise_after_repeat = list(
                    expertise_started
                )
                jobs_after_repeat = list(created_jobs)

                # 3. Incident sur une source de logs :
                #    collecte Katsuyu d'abord, pas expertise
                #    directe concurrente.
                handler(
                    SimpleNamespace(
                        observation=object(),
                    )
                )

                expertise_after_log_source = list(
                    expertise_started
                )
                jobs_after_log_source = list(created_jobs)

        finally:
            os.chdir(previous_directory)

            if service is not None:
                if service.job_repository is not None:
                    service.job_repository.close()

                if service.incident_repository is not None:
                    service.incident_repository.close()

        log_job = (
            jobs_after_log_source[0]
            if len(jobs_after_log_source) == 1
            else None
        )

        checks = [
            (
                "incident sans logs déclenche Tsunade",
                expertise_after_first
                == [str(incident_id)],
            ),
            (
                "incident sans logs ne crée pas de collecte",
                jobs_after_first == [],
            ),
            (
                "observation répétée ne relance pas Tsunade",
                expertise_after_repeat
                == [str(incident_id)],
            ),
            (
                "observation répétée ne crée aucun job",
                jobs_after_repeat == [],
            ),
            (
                "source de logs crée une seule collecte",
                len(jobs_after_log_source) == 1
                and log_job is not None
                and log_job["type"] == "logs.health_check",
            ),
            (
                "collecte reliée au bon incident",
                log_job is not None
                and log_job["parameters"]["sources"]
                == ["infra-01"]
                and log_job["parameters"]["incident_id"]
                == str(log_incident_id),
            ),
            (
                "source de logs ne lance pas expertise directe",
                expertise_after_log_source
                == [str(incident_id)],
            ),
        ]

        return {
            "passed": all(
                passed for _, passed in checks
            ),
            "checks": checks,
            "details": {
                "expertises directes": len(
                    expertise_after_log_source
                ),
                "jobs logs": len(
                    jobs_after_log_source
                ),
                "incident sans logs": str(incident_id),
                "incident avec logs": str(log_incident_id),
            },
        }