"""Read-only recette of the Phase 4 / 9 / 10 additions, after a deployment.

Nothing here changes Konoha: it reads Vision's API (as the browser does) and runs
a few read-only commands on INFRA-01. Each check says what it proved; a check that
cannot be decided yet (the first archive verification comes 30 minutes after the
Agent starts) is reported as *pending*, not as a failure.
"""

from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable

HOST = "192.168.1.10"
USER = "ohanna"
VISION = f"http://{HOST}:8000"
REPORT_DIRECTORY = "/var/lib/ohana-installer/restore-reports"
EXPECTED_RULES = (
    "backup_restore",
    "icloud_session",
    "backup_freshness",
    "adguard_protection",
    "storage_health",
)


@dataclass
class Recette:
    expected_agent: str
    expected_vision: str
    fetch: Callable[[str], Any] = None  # type: ignore[assignment]
    shell: Callable[[str], str] = None  # type: ignore[assignment]
    results: list[tuple[str, str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.fetch = self.fetch or _fetch
        self.shell = self.shell or _ssh

    def record(self, label: str, status: str, detail: str = "") -> None:
        self.results.append((label, status, detail))

    def passed(self) -> bool:
        return all(status != "KO" for _, status, _ in self.results)


def _fetch(path: str) -> Any:
    with urllib.request.urlopen(VISION + path, timeout=15) as response:  # noqa: S310
        return json.load(response)


def _ssh(command: str) -> str:
    completed = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", f"{USER}@{HOST}", command],
        capture_output=True,
        check=False,
        timeout=60,
    )
    return completed.stdout.decode("utf-8", errors="replace").strip()


def run(expected_agent: str, expected_vision: str, **overrides: Any) -> Recette:
    recette = Recette(expected_agent, expected_vision, **overrides)
    _versions(recette)
    _preventive_rules(recette)
    _backups(recette)
    _journal(recette)
    _storage(recette)
    _reports_directory(recette)
    return recette


def _try(recette: Recette, label: str, check: Callable[[], tuple[str, str]]) -> None:
    try:
        status, detail = check()
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        StopIteration,
        urllib.error.URLError,
    ) as error:
        status, detail = "KO", f"{type(error).__name__}: {error}"
    recette.record(label, status, detail)


def _versions(recette: Recette) -> None:
    def vision() -> tuple[str, str]:
        runtime = recette.fetch("/api/runtime/vitals")
        version = str(runtime.get("version"))
        return (
            "OK" if version == recette.expected_vision else "KO",
            f"Vision {version}, attendu {recette.expected_vision}",
        )

    def agent() -> tuple[str, str]:
        vitals = recette.fetch("/api/administration/agent/vitals")
        version = str(((vitals.get("versions") or {}).get("agent") or {}).get("installed"))
        return (
            "OK" if version == recette.expected_agent else "KO",
            f"Agent {version}, attendu {recette.expected_agent}",
        )

    _try(recette, "Version de Vision", vision)
    _try(recette, "Version de l'Agent", agent)


def _preventive_rules(recette: Recette) -> None:
    def rules() -> tuple[str, str]:
        summary = recette.fetch("/api/administration/tsunade/preventive")
        found = {check["id"] for check in summary.get("checks", [])}
        missing = [rule for rule in EXPECTED_RULES if rule not in found]
        if missing:
            return "KO", f"règles absentes : {', '.join(missing)}"
        states = {c["id"]: c["state"] for c in summary["checks"] if c["id"] in EXPECTED_RULES}
        return "OK", ", ".join(f"{k}={v}" for k, v in sorted(states.items()))

    def urgent() -> tuple[str, str]:
        summary = recette.fetch("/api/administration/tsunade/preventive")
        urgent_items = [i["title"] for i in summary.get("watch", []) if i.get("urgent")]
        if urgent_items:
            return "ATTENTION", " ; ".join(urgent_items)
        return "OK", "aucun élément urgent"

    _try(recette, "Règles préventives livrées", rules)
    _try(recette, "Éléments urgents de la maintenance préventive", urgent)


def _backups(recette: Recette) -> None:
    def document() -> tuple[str, str]:
        data = recette.fetch("/api/administration/tsunade/backups/restore-tests")
        targets = data.get("targets", [])
        if not targets:
            return "EN ATTENTE", "aucune cible sauvegardée observée pour l'instant"
        states = ", ".join(f"{t['target']}={t['state']}" for t in targets)
        return "OK", states

    def icloud() -> tuple[str, str]:
        data = recette.fetch("/api/administration/tsunade/backups/restore-tests")
        status = data.get("icloud")
        if status is None:
            return "EN ATTENTE", "première lecture horaire de la session iCloud"
        return (
            "OK" if status["connected"] else "KO",
            f"session {status['state']} (contrôlée {status['checked_at']})",
        )

    def integrity() -> tuple[str, str]:
        data = recette.fetch("/api/administration/tsunade/backups/restore-tests")
        checked = {
            t["target"]: (t.get("integrity") or {}).get("outcome")
            for t in data.get("targets", [])
        }
        if not any(checked.values()):
            return "EN ATTENTE", "première vérification d'archives 30 minutes après le démarrage"
        bad = {t: o for t, o in checked.items() if o not in {None, "ok"}}
        if bad:
            return "KO", ", ".join(f"{t}={o}" for t, o in bad.items())
        return "OK", ", ".join(f"{t}={o or 'pas encore'}" for t, o in sorted(checked.items()))

    _try(recette, "Registre des restaurations", document)
    _try(recette, "État de la session iCloud", icloud)
    _try(recette, "Intégrité des archives relues", integrity)


def _journal(recette: Recette) -> None:
    def httpx() -> tuple[str, str]:
        count = recette.shell(
            "journalctl -u ohana-agent --since '15 min ago' --no-pager | grep -c httpx"
        )
        total = recette.shell(
            "journalctl -u ohana-agent --since '15 min ago' --no-pager | wc -l"
        )
        return (
            "OK" if count.strip() in {"0", ""} else "KO",
            f"{count or 0} ligne(s) httpx sur {total} en 15 minutes",
        )

    def warnings() -> tuple[str, str]:
        count = recette.shell(
            "journalctl -u ohana-agent -u ohana-vision --since '15 min ago' "
            "-p warning --no-pager | grep -vc '^-- '"
        )
        return ("OK" if count.strip() in {"0", ""} else "ATTENTION", f"{count or 0} avertissement(s)")

    _try(recette, "Journal de l'Agent sans lignes httpx", httpx)
    _try(recette, "Aucun avertissement récent", warnings)


def _storage(recette: Recette) -> None:
    def card() -> tuple[str, str]:
        summary = recette.fetch("/api/administration/tsunade/preventive")
        rule = next((c for c in summary["checks"] if c["id"] == "storage_health"), None)
        if rule is None:
            return "KO", "règle storage_health absente"
        nodes = rule.get("nodes", [])
        if not nodes:
            return "EN ATTENTE", "aucune mesure d'écriture SD (premières mesures après quelques minutes)"
        return "OK", nodes[0]["summary"]

    _try(recette, "Mesure d'écriture de la carte SD", card)


def _reports_directory(recette: Recette) -> None:
    def directory() -> tuple[str, str]:
        out = recette.shell(
            f"sudo -n -u ohana-agent sh -c 'if [ -d {REPORT_DIRECTORY} ]; then "
            f"ls {REPORT_DIRECTORY} | wc -l; else echo absent; fi'"
        )
        if out == "absent":
            return "OK", "dossier absent : aucune restauration n'a encore eu lieu"
        return "OK", f"dossier lisible par l'Agent, {out} compte(s) rendu(s)"

    _try(recette, "Dossier des comptes rendus de restauration", directory)


def print_report(recette: Recette) -> None:
    symbols = {"OK": "✓", "KO": "✗", "EN ATTENTE": "…", "ATTENTION": "!"}
    for label, status, detail in recette.results:
        print(f"{symbols.get(status, '?')} {label:<52} {status:<10} {detail}")
    print()
    print("RÉSULTAT : " + ("PASS" if recette.passed() else "ÉCHEC"))
