"""Phase 4: INFRA-01's system updates, certificates and Home Assistant updates.

Real Agent pieces: the background sampler writes one reading per day, the
preventive monitor judges them, and the administration service answers Vision
(detail) and Shizune (essential). The apt simulation, the TLS service and Home
Assistant are simulated; the root helpers of the Installer are replaced by a
fake ``systemctl``. The Agent never installs, renews or restarts anything: it
writes a request, and only the owner's confirmed click reaches apt.
"""

from __future__ import annotations

import socket
import ssl
import tempfile
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from ohana_agent.api.service import AdministrationService
from ohana_agent.host.system_updates import SystemUpdateRequester
from ohana_agent.infrastructure.repository import InfrastructureConfigurationRepository
from ohana_agent.tsunade.incidents import TsunadeIncidentRepository
from ohana_agent.tsunade.preventive import TsunadePreventiveMonitor
from ohana_agent.tsunade.preventive_expiry import ExpirySampler, probe_certificate

PARIS = ZoneInfo("Europe/Paris")


def _certificate(directory: Path, *, days: int) -> None:
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "bank.ohana.lan")])
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(UTC) - timedelta(days=1))
        .not_valid_after(datetime.now(UTC) + timedelta(days=days))
        .sign(key, hashes.SHA256())
    )
    (directory / "bank.crt").write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    (directory / "bank.key").write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )


def _tls_service(directory: Path) -> tuple[socket.socket, threading.Thread]:
    """A local TLS service presenting the certificate, like Ohana-Bank's nginx."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(directory / "bank.crt", directory / "bank.key")
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)

    def serve() -> None:
        # One connection per daily reading, until the scenario closes the socket.
        while True:
            try:
                connection, _address = server.accept()
            except OSError:
                return
            try:
                with context.wrap_socket(connection, server_side=True):
                    pass
            except OSError:
                pass

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    return server, thread


def _titles(summary: dict) -> list[str]:
    return [item["title"] for item in summary["watch"]]


def run() -> dict:
    checks: list[tuple[str, bool]] = []
    details: dict[str, str] = {}
    now = datetime.now(PARIS).replace(microsecond=0)
    with tempfile.TemporaryDirectory(prefix="ohana-sandbox-system-maintenance-") as tmp:
        root = Path(tmp)
        _certificate(root, days=20)
        server, thread = _tls_service(root)
        port = server.getsockname()[1]

        # Day by day: the sampler reads, the monitor judges.
        state = {"security_count": 0, "pending_count": 0, "reboot_required": False,
                 "lists_stale": False, "lists_age_days": 0.5}
        clock = {"now": now - timedelta(days=9)}
        ha_updates = [
            {"entity_id": "update.mosquitto_broker", "state": "on",
             "attributes": {"title": "Mosquitto broker", "installed_version": "6.5.0",
                            "latest_version": "6.5.2"}},
            {"entity_id": "update.core", "state": "off", "attributes": {}},
        ]
        sampler = ExpirySampler(
            record_snapshot=lambda *args: monitor.record_snapshot(*args),
            system_reader=lambda: dict(state),
            certificates=lambda: [
                ("Ohana-Bank", lambda: probe_certificate("127.0.0.1", port, "bank.ohana.lan"))
            ],
            home_assistant_states=lambda: ha_updates,
            clock=lambda: clock["now"],
        )
        incidents = TsunadeIncidentRepository(root / "control.db")
        monitor = TsunadePreventiveMonitor(root / "control.db")
        service = AdministrationService(
            infrastructure_repository=InfrastructureConfigurationRepository(
                root / "infrastructure.yaml"
            ),
            incident_repository=incidents,
            preventive_monitor=monitor,
            job_repository=None,
        )
        try:
            # Nothing read yet: the rules must say so, never reassure.
            unknown = {
                check["id"]: check["state"]
                for check in service.read_preventive_summary()["checks"]
            }

            # Security fixes appear on day 0 and stay pending for 9 days.
            state.update(security_count=2, pending_count=5, reboot_required=True)
            for _day in range(10):
                sampler.sample()
                clock["now"] += timedelta(days=1)
            clock["now"] = now
            pending = monitor.summary(now=now)
            detail = service.read_preventive_summary()
            essential = service.read_companion_summary()["preventive"]

            # Installing them restarts the clock; lists left stale are flagged at once.
            state.update(security_count=0, pending_count=0, reboot_required=False)
            sampler.sample()
            installed = monitor.summary(now=now)
            state.update(lists_stale=True, lists_age_days=26.0)
            sampler.sample()
            stale = monitor.summary(now=now)
            muted = monitor.mute("system_updates", "lists-stale", days=7, now=now)
            after_mute = monitor.summary(now=now)

            # The owner's click: refused on stale lists, honoured, never doubled.
            systemd = root / "systemd"
            systemd.mkdir()
            for stem in ("system-refresh", "system-upgrade"):
                (systemd / f"ohana-{stem}.path").write_text("", encoding="utf-8")
            systemctl = root / "systemctl"
            systemctl.write_text("", encoding="utf-8")
            running = {"upgrade": False}

            def fake_systemctl(command, **_kwargs):
                active = running["upgrade"] and "upgrade" in command[2]
                return SimpleNamespace(
                    stdout=f"ActiveState={'activating' if active else 'inactive'}\n"
                    "Result=success\nExecMainStartTimestampMonotonic=0\n",
                    returncode=0,
                )

            requester = SystemUpdateRequester(
                request_directory=root / "run",
                systemd_directory=systemd,
                systemctl_path=systemctl,
                runner=fake_systemctl,
            )
            actions = AdministrationService(
                infrastructure_repository=InfrastructureConfigurationRepository(
                    root / "infrastructure.yaml"
                ),
                system_updates_reader=lambda: dict(state, pending_count=3),
                system_update_requester=requester,
            )
            try:
                actions.request_system_update("upgrade")
                refused_stale = False
            except ValueError:
                refused_stale = True
            refresh = actions.request_system_update("refresh")
            state.update(lists_stale=False)
            upgrade = actions.request_system_update("upgrade")
            running["upgrade"] = True
            busy = actions.request_system_update("refresh")
            requests = sorted(path.name for path in (root / "run").iterdir())
        finally:
            monitor.close()
            incidents.close()
            server.close()
            thread.join(timeout=5)

    security = [i for i in pending["watch"] if i["subject"] == "security-updates"]
    certificate = [i for i in pending["watch"] if i["rule"] == "tls_certificates"]
    checks += [
        (
            "sans relevé : les trois règles disent « données insuffisantes »",
            {unknown[key] for key in ("system_updates", "tls_certificates", "ha_updates")}
            == {"insufficient_data"},
        ),
        (
            "correctifs de sécurité en attente depuis 9 jours : signalés",
            len(security) == 1 and "depuis 9 jours" in security[0]["title"]
            and security[0]["urgent"] is False,
        ),
        (
            "redémarrage requis depuis 9 jours : signalé",
            any(i["subject"] == "reboot-required" for i in pending["watch"]),
        ),
        (
            "certificat de Bank lu par sonde TLS : expire dans 20 jours",
            len(certificate) == 1
            and any(f"expirant dans {days} jours" in certificate[0]["title"] for days in (19, 20)),
        ),
        (
            "mise à jour Home Assistant seulement si l'entité est « on » depuis 14 jours",
            all(i["rule"] != "ha_updates" for i in pending["watch"]),
        ),
        (
            "Vision lit les trois règles ; Shizune l'essentiel sans preuves",
            {"system_updates", "tls_certificates", "ha_updates"}
            <= {check["id"] for check in detail["checks"]}
            and any("sécurité" in w["title"] for w in essential["watch"])
            and "evidence" not in str(essential),
        ),
        (
            "mises à jour installées : l'attente repart à zéro",
            all(i["subject"] != "security-updates" for i in installed["watch"]),
        ),
        (
            "listes périmées de 26 jours : urgent aussitôt",
            any(i["subject"] == "lists-stale" and i["urgent"] for i in stale["watch"]),
        ),
        (
            "sourdine acceptée pour la nouvelle règle",
            muted["rule"] == "system_updates"
            and all(i["subject"] != "lists-stale" for i in after_mute["watch"]),
        ),
        (
            "mise à jour refusée sur listes périmées",
            refused_stale,
        ),
        (
            "demandes écrites pour l'assistant, jamais exécutées par l'Agent",
            refresh["started"] is True and upgrade["started"] is True
            and requests == ["system-refresh.request", "system-upgrade.request"],
        ),
        (
            "demande ignorée pendant qu'apt travaille",
            busy == {"started": False, "busy": True, "action": "refresh"},
        ),
        (
            "aucune réparation automatique",
            pending["automatic_actions"] is False,
        ),
    ]
    details["portée"] = (
        "Agent, moniteur préventif et SQLite locaux ; service TLS local réel ; "
        "apt, Home Assistant et systemctl simulés ; aucun assistant root"
    )
    return {
        "passed": all(value for _, value in checks),
        "checks": checks,
        "details": details,
    }
