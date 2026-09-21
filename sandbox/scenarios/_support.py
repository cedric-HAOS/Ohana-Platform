from __future__ import annotations

import json
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from ohana_agent.api.service import AdministrationService
from ohana_agent.infrastructure.repository import (
    InfrastructureConfigurationRepository,
)
from ohana_agent.jobs.repository import DistributedJobRepository
from ohana_agent.observation import Observation, ObservationStatus
from ohana_agent.tsunade.expertise import TsunadeExpertiseService
from ohana_agent.tsunade.incidents import TsunadeIncidentRepository


class SandboxClock:
    def __init__(self) -> None:
        self.current = datetime.now(ZoneInfo("Europe/Paris"))

    def __call__(self) -> datetime:
        return self.current

    def advance(self, **kwargs) -> datetime:
        self.current += timedelta(**kwargs)
        return self.current


class NoProbes:
    def execute(self, payload):
        raise AssertionError(
            "Le Sandbox ne doit exécuter aucune sonde réelle."
        )


@dataclass
class SandboxEnvironment:
    root: Path
    clock: SandboxClock
    jobs: DistributedJobRepository
    incidents: TsunadeIncidentRepository
    expertise: TsunadeExpertiseService
    service: AdministrationService
    incident: object


def ai_result() -> dict:
    return {
        "verdict": "INSUFFICIENT_CONTEXT",
        "generated_at": datetime.now(
            ZoneInfo("Europe/Paris")
        ).isoformat(),
        "model_id": "sandbox",
        "model_sha256": "a" * 64,
        "summary": (
            "Des journaux supplémentaires permettraient "
            "de vérifier la cause."
        ),
        "missing_context": ["journaux ciblés"],
        "recommended_investigation": [
            "Collecter les journaux autour des timeouts."
        ],
        "metrics": {
            "prompt_tokens": 1,
            "completion_tokens": 1,
            "ttft_ms": 1,
            "tokens_per_second": 1,
            "duration_seconds": 1,
        },
    }


@contextmanager
def environment():
    with tempfile.TemporaryDirectory(
        prefix="ohana-sandbox-"
    ) as temporary:
        root = Path(temporary)
        clock = SandboxClock()

        jobs = DistributedJobRepository(
            root / "jobs.db",
            clock=clock,
        )

        incidents = TsunadeIncidentRepository(
            root / "incidents.db"
        )

        expertise = TsunadeExpertiseService(
            incidents=incidents,
            investigations=NoProbes(),
            ai_dispatcher=jobs.create,
        )

        service = AdministrationService(
            infrastructure_repository=(
                InfrastructureConfigurationRepository(
                    root / "infra.yaml"
                )
            ),
            job_repository=jobs,
            incident_repository=incidents,
            expertise_service=expertise,
            log_sources=("ha-01",),
        )

        incident = incidents.process(
            Observation(
                node="ha-01",
                service="logs",
                capability="logs.health",
                status=ObservationStatus.DEGRADED,
                success=False,
                message="Connection timeout",
                source="logs.health",
                timestamp=clock(),
                metadata={
                    "findings": [
                        {
                            "source": "ha-01",
                            "signature": "timeout",
                            "category": "timeout",
                            "occurrences": 2,
                            "summary": "Connection timeout",
                            "severity": "error",
                            "trend": "new",
                        }
                    ]
                },
            )
        )

        jobs.register_worker(
            {
                "worker_id": "sandbox-worker",
                "platform": "Sandbox",
                "worker_version": "dev",
                "capabilities": [
                    "ai.inference",
                    "logs.investigate",
                ],
            }
        )

        sandbox = SandboxEnvironment(
            root=root,
            clock=clock,
            jobs=jobs,
            incidents=incidents,
            expertise=expertise,
            service=service,
            incident=incident,
        )

        try:
            yield sandbox
        finally:
            jobs.close()
            incidents.close()


def poll(sandbox: SandboxEnvironment):
    response = sandbox.service.next_worker_job(
        {
            "worker_id": "sandbox-worker",
            "supported_types": [
                "ai.inference",
                "logs.investigate",
            ],
        }
    )
    return response.job


def propose(sandbox: SandboxEnvironment):
    job = sandbox.jobs.create(
        {
            "job_id": str(uuid4()),
            "created_at": sandbox.clock().isoformat(),
            "type": "ai.inference",
            "timeout": 900,
            "parameters": {
                "incident_id": str(
                    sandbox.incident.incident_id
                ),
                "question": "Pourquoi ?",
                "evidence": [
                    {
                        "source": "shikamaru.observation",
                        "content": json.dumps(
                            {
                                "last_observed_at": (
                                    sandbox.incident
                                    .last_observed_at
                                    .isoformat()
                                )
                            }
                        ),
                    }
                ],
            },
        }
    )

    claimed = poll(sandbox)

    if claimed is None:
        raise AssertionError(
            "Le worker Sandbox n'a reçu aucun job IA."
        )

    if claimed.job_id != job.job_id:
        raise AssertionError(
            "Le worker Sandbox a reçu un job inattendu."
        )

    sandbox.service.complete_job(
        str(job.job_id),
        {
            "worker_id": "sandbox-worker",
            "attempt": claimed.attempt,
            "status": "SUCCEEDED",
            "result": ai_result(),
        },
    )

    return job


def authorize(sandbox: SandboxEnvironment):
    requests = (
        sandbox.service
        .read_companion_requests()
        .requests
    )

    if len(requests) != 1:
        raise AssertionError(
            "Une demande d'autorisation était attendue, "
            f"{len(requests)} reçue(s)."
        )

    request = requests[0]

    sandbox.service.respond_companion_request(
        str(request.request_id),
        "sandbox-operator",
        {"choice": "AUTHORIZE"},
    )

    return request


def job_counts(
    sandbox: SandboxEnvironment,
) -> dict[str, int]:
    return {
        "ai.inference": sandbox.jobs.count(
            "ai.inference"
        ),
        "logs.investigate": sandbox.jobs.count(
            "logs.investigate"
        ),
    }


def diagnostic_count(
    sandbox: SandboxEnvironment,
) -> int:
    incident = sandbox.incidents.get(
        sandbox.incident.incident_id
    )

    return sum(
        event.kind == "diagnostic"
        for event in incident.events
    )