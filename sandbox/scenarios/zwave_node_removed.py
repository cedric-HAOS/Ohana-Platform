"""A node removed from Z-Wave JS leaves the topology, its layout and Tsunade.

On 15 November the Sonnette (node 25) was removed from Z-Wave JS. The
discovery dropped it from the topology devices and links but not from the
layout saved in infrastructure.yaml, so Vision rejected every infrastructure
snapshot (HTTP 422, "topology layouts reference unknown devices") and the
Infrastructure view stayed empty after Vision restarted. Its silence incident
also stayed active forever: no observation could resolve a node that no
longer exists.

The Agent is built by the production bootstrap (real discovery handler, real
Tsunade repository and wiring); each snapshot it sends is validated by
Vision's own request model and topology mapper. Only the Z-Wave controller
answers are simulated, as the discovery events the Z-Wave plugin publishes.
"""

from __future__ import annotations

import os
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch
from uuid import uuid4

import ohana_agent
import yaml
from ohana_agent.core.events import EventBus
from ohana_agent.observation import Observation, ObservationStatus
from ohana_agent.plugins.zwave.discovery import ZWaveDiscoveryHandler
from ohana_agent.runtime.bootstrap import build_production_agent
from ohana_agent.tsunade.expertise import TsunadeExpertiseService
from ohana_vision.web.infrastructure_mapper import InfrastructureMapper
from ohana_vision.web.infrastructure_request import InfrastructureRequest

CONTROLLER = "zwave-primary"
GATEWAY = "rpi-zwave"
KEPT = f"zwave-{CONTROLLER}-node-2"
REMOVED = f"zwave-{CONTROLLER}-node-25"


class VisionValidator:
    """Accept or reject snapshots exactly as Vision's PUT /api/infrastructure."""

    def __init__(self) -> None:
        self.accepted: list[dict[str, Any]] = []
        self.rejected: list[str] = []

    def check(self, payload: dict[str, Any]) -> bool:
        try:
            InfrastructureMapper.to_topology(InfrastructureRequest.model_validate(payload))
        except ValueError as error:  # pydantic ValidationError is a ValueError.
            errors = getattr(error, "errors", None)
            message = errors()[0]["msg"] if callable(errors) else str(error)
            self.rejected.append(message[:200])
            return False
        self.accepted.append(payload)
        return True

    def send_infrastructure(self, payload: dict[str, Any]) -> None:
        self.check(payload)

    def send_observation(self, payload: dict[str, Any]) -> None:
        del payload


def _managed(node_id: int, label: str) -> tuple[dict, dict]:
    device_id = f"zwave-{CONTROLLER}-node-{node_id}"
    metadata = {"managed_by": "zwave_discovery", "controller_service_id": CONTROLLER}
    device = {
        "id": device_id,
        "label": label,
        "kind": "zwave_module",
        "metadata": {**metadata, "radio_kind": "zwave", "zwave_node_id": node_id},
    }
    link = {
        "id": f"{GATEWAY}-{device_id}",
        "source": GATEWAY,
        "target": device_id,
        "kind": "zwave",
        "direction": "bidirectional",
        "label": "Z-Wave",
        "metadata": metadata,
    }
    return device, link


def _infrastructure(agent_root: Path, target: Path) -> None:
    """The repository topology as saved from Vision once both nodes were known."""
    data = yaml.safe_load(
        (agent_root / "config" / "infrastructure.yaml").read_text(encoding="utf-8")
    )
    topology = data["topology"]
    for column, (node_id, label) in enumerate(((2, "Prise"), (25, "Sonnette"))):
        device, link = _managed(node_id, label)
        topology["devices"].append(device)
        topology["links"].append(link)
        topology["layouts"][0]["positions"][device["id"]] = {
            "column": 20 + column,
            "row": 0,
        }
    target.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


def _discovery(nodes: list[int] | None, at: datetime) -> SimpleNamespace:
    metadata: dict[str, Any] = {"discovery_complete": nodes is not None}
    # Node 25 is silent, as the Sonnette was: its incident stays open.
    metadata["nodes"] = [
        {
            "node_id": node_id,
            "status": "alive",
            "name": f"Nœud {node_id}",
            "silent": node_id == 25,
            "last_seen_age_seconds": 90_000 if node_id == 25 else 30,
            "silence_threshold_minutes": 1440,
        }
        for node_id in nodes or []
    ]
    if nodes is not None:
        metadata["home_id"] = "3928570345"
    return SimpleNamespace(
        observation=SimpleNamespace(
            capability="zwave.status",
            service=CONTROLLER,
            timestamp=at,
            metadata=metadata,
        )
    )


def run() -> dict:
    agent_root = Path(ohana_agent.__file__).resolve().parents[2]
    checks: list[tuple[str, bool]] = []
    details: dict[str, str] = {}
    vision = VisionValidator()

    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-zwave-removed-") as tmp:
        root = Path(tmp)
        (root / "management.token").write_text("management-secret\n", encoding="utf-8")
        (root / "katsuyu.token").write_text("worker-secret\n", encoding="utf-8")
        infrastructure = root / "infrastructure.yaml"
        _infrastructure(agent_root, infrastructure)
        application = root / "shikamaru.yaml"
        application.write_text(
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
  token_file: {(root / "management.token").as_posix()}

  jobs:
    enabled: true
    database_path: {(root / "distributed-jobs.db").as_posix()}
    worker_token_file: {(root / "katsuyu.token").as_posix()}

  dhcp:
    enabled: false
""",
            encoding="utf-8",
        )

        handlers: list[ZWaveDiscoveryHandler] = []
        original_subscribe = EventBus.subscribe

        def capture(self: EventBus, event_type: type[Any], handler: Any) -> None:
            owner = getattr(handler, "__self__", None)
            if isinstance(owner, ZWaveDiscoveryHandler):
                handlers.append(owner)
            original_subscribe(self, event_type, handler)

        previous_directory = Path.cwd()
        service = None
        try:
            os.chdir(agent_root)
            with (
                patch.object(EventBus, "subscribe", new=capture),
                # No AI or investigation: only the incident lifecycle matters.
                patch.object(TsunadeExpertiseService, "start", new=lambda *_a, **_k: None),
            ):
                agent = build_production_agent(
                    application_config_path=application,
                    infrastructure_config_path=infrastructure,
                    vision_client=vision,  # type: ignore[arg-type]
                )
                service = agent.administration_runtime.service
                incidents = service.incident_repository
                handler = handlers[0] if len(handlers) == 1 else None
                if handler is None or incidents is None:
                    raise AssertionError("Découverte Z-Wave ou Tsunade non câblés.")

                checks.append(
                    (
                        "Topologie enregistrée (nœuds 2 et 25 placés) acceptée par Vision",
                        vision.check(agent.infrastructure_payload),
                    )
                )

                started = datetime.now(UTC).replace(microsecond=0)
                silent = incidents.process(
                    Observation(
                        node=REMOVED,
                        service=REMOVED,
                        capability="zwave.node.alive",
                        status=ObservationStatus.DEGRADED,
                        success=False,
                        message="Sonnette n'a pas donné signe de vie depuis 1500 min.",
                        source="zwave.node.alive",
                        id=uuid4(),
                        timestamp=started,
                        metadata={"target_type": "device", "device_id": REMOVED},
                    )
                )
                if silent is None:
                    raise AssertionError("L'incident de silence n'a pas été ouvert.")

                handler.handle(_discovery(None, started + timedelta(minutes=2)))
                checks.append(
                    (
                        "Contrôleur injoignable : l'incident du nœud 25 reste ouvert",
                        incidents.get(silent.incident_id).state == "active",
                    )
                )

                handler.handle(_discovery([2, 25], started + timedelta(minutes=4)))
                checks.append(
                    (
                        "Nœud 25 encore présent mais silencieux : incident toujours ouvert",
                        incidents.get(silent.incident_id).state == "active",
                    )
                )
                handler.handle(_discovery([2], started + timedelta(minutes=6)))

                last = vision.accepted[-1] if vision.accepted else {}
                checks += [
                    (
                        "Nœud 25 retiré de Z-Wave JS : Vision accepte chaque instantané",
                        not vision.rejected,
                    ),
                    (
                        "Le nœud 25 a quitté équipements, liens et disposition",
                        bool(last) and REMOVED not in repr(last["topology"]),
                    ),
                    (
                        "Le nœud 2 garde sa position dans la disposition",
                        bool(last)
                        and KEPT in last["topology"]["layouts"][0]["positions"],
                    ),
                ]
                closed = incidents.get(silent.incident_id)
                checks.append(
                    (
                        "Tsunade clôt l'incident du nœud retiré, sans le déclarer sain",
                        closed.state == "resolved"
                        and closed.events[-1].kind == "monitoring_removed",
                    )
                )
                details["incident"] = f"{REMOVED} / zwave.node.alive → {closed.state}"
        finally:
            os.chdir(previous_directory)
            if service is not None:
                if service.job_repository is not None:
                    service.job_repository.close()
                if service.incident_repository is not None:
                    service.incident_repository.close()
                if getattr(service, "preventive_monitor", None) is not None:
                    service.preventive_monitor.close()

    details["Vision"] = (
        f"{len(vision.accepted)} instantané(s) accepté(s), {len(vision.rejected)} refusé(s)"
        + (f" : {vision.rejected[0]}" if vision.rejected else "")
    )
    details["portée"] = (
        "Bootstrap Agent, découverte Z-Wave, Tsunade et validation Vision réels ; "
        "réponses du contrôleur Z-Wave simulées"
    )
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
