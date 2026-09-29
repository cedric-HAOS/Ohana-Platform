"""A frozen Agent becomes unavailable in Home Assistant.

Phase 5 reserve, 29 September: an Agent whose process lives but whose loop
is blocked keeps its MQTT session, so the broker never sends its "offline"
will; only Vision's banner showed it. The user's Home Assistant automation
notifies after ten minutes of unavailable Ohana sensors.

The real Agent vitals, liveness rule and MQTT Home Assistant publisher run
with a simulated clock and broker. The stand-in Home Assistant applies
``expire_after`` from the discovery payload the way Home Assistant does: a
sensor without a message for that long becomes unavailable.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from ohana_agent.plugins.mqtt.config import (
    MQTTBrokerConfig,
    MQTTConfig,
    MQTTHomeAssistantConfig,
)
from ohana_agent.plugins.mqtt.home_assistant_publisher import MQTTHomeAssistantPublisher
from ohana_agent.runtime.vitals import AgentVitals, silent_agent_components

from scenarios.icloud_connectivity_mqtt import _infrastructure

SUMMARY = "ohana/health/summary"
ALERTS_CONFIG = "homeassistant/sensor/ohana_active_alerts/config"


class _PublishInfo:
    rc = 0


class _HomeAssistant:
    """paho-like client; Home Assistant's view of the summary sensor."""

    def __init__(self, clock: list[float]) -> None:
        self.clock = clock
        self.on_connect = None
        self.on_disconnect = None
        self.expire_after: float | None = None
        self.last_summary_at: float | None = None
        self.offline = False

    def username_pw_set(self, *_args) -> None:
        return None

    def will_set(self, *_args, **_kwargs) -> None:
        return None

    def connect(self, *_args, **_kwargs) -> int:
        return 0

    def loop_start(self) -> None:
        self.on_connect(self, None, None, 0, None)

    def publish(self, topic, payload, *, qos, retain) -> _PublishInfo:
        del qos, retain
        if topic == ALERTS_CONFIG and payload:
            self.expire_after = json.loads(payload).get("expire_after")
        elif topic == SUMMARY:
            self.last_summary_at = self.clock[0]
        elif topic == "ohana/status":
            self.offline = payload == "offline"
        return _PublishInfo()

    def disconnect(self) -> None:
        return None

    def loop_stop(self) -> None:
        return None

    def available(self) -> bool:
        if self.offline or self.last_summary_at is None:
            return False
        if self.expire_after is None:
            return True
        return self.clock[0] - self.last_summary_at < self.expire_after


def run() -> dict:
    checks = []
    details = {}
    clock = [0.0]
    vitals = AgentVitals(
        monotonic_clock=lambda: clock[0],
        wall_clock=lambda: datetime(2026, 9, 29, 10, 0, tzinfo=UTC),
    )
    vitals.declare("scheduler", label="Planificateur", max_silence_seconds=300)
    vitals.declare("vision_delivery", label="Livraison à Vision", max_silence_seconds=300)
    vitals.declare("tsunade", label="Tsunade", max_silence_seconds=300)
    vitals.declare("administration", label="API d'administration", max_silence_seconds=60)
    home_assistant = _HomeAssistant(clock)
    publisher = MQTTHomeAssistantPublisher(
        config=MQTTConfig(
            brokers=[MQTTBrokerConfig(name="mqtt-primary", address="192.168.1.247")],
            home_assistant=MQTTHomeAssistantConfig(
                enabled=True, discovery_enabled=True, heartbeat_seconds=60
            ),
        ),
        infrastructure=_infrastructure(),
        client_factory=lambda _client_id: home_assistant,
        monotonic_clock=lambda: clock[0],
    )
    publisher.set_liveness(lambda: silent_agent_components(vitals))
    publisher.start()

    def run_for(seconds: int, beating: tuple[str, ...]) -> None:
        # The Agent tick thread keeps running; only the listed components beat.
        for _ in range(0, seconds, 10):
            clock[0] += 10
            for component in beating:
                vitals.beat(component)
            publisher.tick()

    everything = ("scheduler", "vision_delivery", "tsunade", "administration")
    run_for(600, everything)
    checks.append(
        (
            "Agent sain : capteurs Ohana disponibles dans Home Assistant",
            home_assistant.available(),
        )
    )
    details["expire_after (s)"] = home_assistant.expire_after

    run_for(900, ("scheduler", "tsunade", "administration"))
    checks.append(
        (
            "Vision indisponible 15 min : l'Agent reste disponible (incident à part)",
            home_assistant.available(),
        )
    )

    frozen_at = clock[0]
    unavailable_after = None
    for _ in range(0, 900, 10):
        run_for(10, ("scheduler", "vision_delivery", "tsunade"))
        if unavailable_after is None and not home_assistant.available():
            unavailable_after = clock[0] - frozen_at
    details["indisponible après (s)"] = unavailable_after
    checks += [
        (
            "boucle d'administration figée, processus vivant : capteurs "
            "indisponibles sans message offline",
            unavailable_after is not None and not home_assistant.offline,
        ),
        (
            "indisponible en moins de 10 min (silence 60 s + expiration 300 s)",
            unavailable_after is not None and unavailable_after <= 600,
        ),
    ]

    run_for(120, everything)
    checks.append(
        (
            "boucle revenue : capteurs de nouveau disponibles",
            home_assistant.available(),
        )
    )
    publisher.stop()
    details["portée"] = (
        "vitaux, règle de vivacité et publieur MQTT réels de l'Agent ; horloge, "
        "broker et Home Assistant simulés"
    )
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
