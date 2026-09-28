"""The iCloud session state reaches Home Assistant through MQTT.

Production, 28 September: the rclone iCloud session of INFRA-01 had expired
("trust token expired, please reauth", HTTP 421 "Invalid global session") and
nothing reported it until an update tried to copy the age recovery identity.

The real Agent reporter and MQTT Home Assistant publisher run here with a
simulated rclone and broker: expired session, reconnection, then a slow iCloud
that must not block the scheduler tick nor start a second check.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from ohana_agent.configuration.infrastructure import InfrastructureConfig
from ohana_agent.plugins.backup.config import BackupConfig
from ohana_agent.plugins.backup.icloud_connectivity import (
    ICloudConnectivityProbe,
    ICloudConnectivityReporter,
)
from ohana_agent.plugins.mqtt.config import (
    MQTTBrokerConfig,
    MQTTConfig,
    MQTTHomeAssistantConfig,
)
from ohana_agent.plugins.mqtt.home_assistant_publisher import MQTTHomeAssistantPublisher

TOPIC = "ohana/icloud/connectivity"
EXPIRED = (
    'CRITICAL: Failed to create file system for "icloud:": '
    "trust token expired, please reauth"
)
MISDIRECTED = (
    "ERROR : HTTP error 421 (421 Misdirected Request) returned body: "
    '"{\\"reason\\":\\"Invalid global session\\",\\"error\\":2}"'
)


@dataclass
class _PublishInfo:
    rc: int = 0


class _Broker:
    """paho-like client keeping every publication."""

    def __init__(self) -> None:
        self.on_connect = None
        self.on_disconnect = None
        self.published: list[tuple[str, str, bool]] = []

    def username_pw_set(self, *_args) -> None:
        return None

    def will_set(self, *_args, **_kwargs) -> None:
        return None

    def connect(self, *_args, **_kwargs) -> int:
        return 0

    def loop_start(self) -> None:
        self.on_connect(self, None, None, 0, None)

    def publish(self, topic, payload, *, qos, retain) -> _PublishInfo:
        del qos
        self.published.append((topic, payload, retain))
        return _PublishInfo()

    def disconnect(self) -> None:
        return None

    def loop_stop(self) -> None:
        return None

    def states(self) -> list[dict]:
        return [json.loads(payload) for topic, payload, _ in self.published if topic == TOPIC]


class _Rclone:
    """Scripted rclone answers: (exit code, stderr, seconds before answering)."""

    def __init__(self) -> None:
        self.answers: list[tuple[int, str, float]] = []
        self.calls: list[list[str]] = []

    def __call__(self, command, **_kwargs):
        self.calls.append(command)
        code, stderr, delay = self.answers.pop(0)
        time.sleep(delay)
        return subprocess.CompletedProcess(command, code, "", stderr)


def _infrastructure() -> InfrastructureConfig:
    return InfrastructureConfig.model_validate(
        {
            "infrastructure": {"id": "ohana-house", "name": "Ohana House"},
            "nodes": [
                {
                    "id": "infra-01",
                    "name": "INFRA-01",
                    "endpoint": {"type": "ip", "address": "192.168.1.10"},
                }
            ],
            "services": [
                {
                    "id": "dns-primary",
                    "name": "DNS primaire",
                    "type": "dns",
                    "node": "infra-01",
                    "critical": True,
                }
            ],
            "topology": {
                "devices": [
                    {
                        "id": "infra-01-device",
                        "label": "INFRA-01",
                        "kind": "server",
                        "node": "infra-01",
                    }
                ]
            },
        }
    )


def _wait(reporter: ICloudConnectivityReporter) -> None:
    check = reporter._running_check
    if check is not None:
        check.join(10)


def run() -> dict:
    checks = []
    details = {}
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-icloud-") as directory:
        root = Path(directory)
        (root / "rclone").write_text("", encoding="utf-8")
        (root / "rclone.conf").write_text("[icloud]\ntype = iclouddrive\n", encoding="utf-8")
        broker = _Broker()
        publisher = MQTTHomeAssistantPublisher(
            config=MQTTConfig(
                brokers=[MQTTBrokerConfig(name="mqtt-primary", address="192.168.1.247")],
                home_assistant=MQTTHomeAssistantConfig(
                    enabled=True, discovery_enabled=True, heartbeat_seconds=60
                ),
            ),
            infrastructure=_infrastructure(),
            client_factory=lambda _client_id: broker,
            agent_version="sandbox",
        )
        publisher.start()
        rclone = _Rclone()
        clock = [0.0]
        reporter = ICloudConnectivityReporter(
            ICloudConnectivityProbe(
                BackupConfig(
                    rclone_binary=str(root / "rclone"),
                    rclone_config_path=str(root / "rclone.conf"),
                ),
                runner=rclone,
            ),
            sinks=(publisher.publish_icloud_connectivity,),
            monotonic_clock=lambda: clock[0],
        )

        # 1. Agent start: the session has expired, as on 28 September.
        rclone.answers.append((1, EXPIRED, 0.0))
        reporter.start()
        _wait(reporter)
        discovery = {
            topic: json.loads(payload)
            for topic, payload, _ in broker.published
            if topic.endswith("/config") and payload
        }
        binary = discovery.get("homeassistant/binary_sensor/ohana_icloud_connectivity/config")
        state_sensor = discovery.get("homeassistant/sensor/ohana_icloud_state/config")
        first = broker.states()[-1] if broker.states() else {}
        checks += [
            (
                "Home Assistant découvre « Connexion iCloud » et « État iCloud » sur "
                "l'appareil Ohana Platform",
                binary is not None
                and state_sensor is not None
                and binary["device"]["name"] == "Ohana Platform"
                and binary["device_class"] == "connectivity"
                and binary["state_topic"] == TOPIC
                and state_sensor["device_class"] == "enum"
                and "session_expired" in state_sensor["options"],
            ),
            (
                "démarrage : jeton iCloud expiré publié (session_expired), message retenu",
                first.get("state") == "session_expired"
                and first.get("connected") is False
                and "please reauth" in (first.get("detail") or "")
                and all(retain for topic, _, retain in broker.published if topic == TOPIC),
            ),
        ]

        # 2. One hour later, after the reconnection in Vision.
        clock[0] += 3600
        rclone.answers.append((0, "", 0.0))
        reporter.tick()
        _wait(reporter)
        reconnected = broker.states()[-1]
        checks.append(
            (
                "une heure après la reconnexion : connected, dernière réussite en "
                "heure de Paris",
                reconnected["state"] == "connected"
                and reconnected["connected"] is True
                and reconnected["last_success_at"] == reconnected["checked_at"]
                and reconnected["checked_at"].endswith(("+02:00", "+01:00")),
            )
        )

        # 3. iCloud answers slowly: the scheduler tick must not wait for it.
        clock[0] += 3600
        rclone.answers.append((1, MISDIRECTED, 2.0))
        started = time.monotonic()
        reporter.tick()
        tick_seconds = time.monotonic() - started
        clock[0] += 3600
        reporter.tick()  # due again while the slow check still runs
        _wait(reporter)
        slow = broker.states()[-1]
        details["durée du tick pendant un rclone de 2 s"] = f"{tick_seconds:.3f} s"
        checks += [
            (
                "un iCloud lent ne bloque pas le tick du planificateur (< 0,5 s)",
                tick_seconds < 0.5,
            ),
            (
                "pas de second contrôle tant que le premier tourne",
                len(rclone.calls) == 3,
            ),
            (
                "HTTP 421 « Invalid global session » : session_expired, dernière "
                "réussite conservée",
                slow["state"] == "session_expired"
                and slow["last_success_at"] == reconnected["checked_at"],
            ),
        ]

        # 4. The broker restarts: the last state is announced again.
        before = len(broker.states())
        broker.on_connect(broker, None, None, 0, None)
        checks.append(
            (
                "reconnexion MQTT : le dernier état iCloud est republié",
                len(broker.states()) == before + 1
                and broker.states()[-1]["state"] == "session_expired",
            )
        )
        details["appels rclone"] = " ; ".join(" ".join(call[1:3]) for call in rclone.calls)
        details["publications iCloud"] = len(broker.states())
        reporter.stop()
        publisher.stop()
    details["portée"] = (
        "Contrôle iCloud et publieur MQTT réels de l'Agent ; rclone et broker simulés"
    )
    details["limites"] = "Aucun appel iCloud réel ; rendu des modèles Home Assistant non évalué"
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
