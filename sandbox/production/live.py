"""Read-only reports on Konoha for live validations and hardening checks."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

HOST = "192.168.1.10"
USER = "ohanna"
JOBS_DATABASE = "/var/lib/ohana-agent/distributed-jobs.db"


def jobs_report(days: int) -> dict:
    """Aggregate the distributed jobs of the last ``days`` days on INFRA-01."""
    script = Path(__file__).with_name("remote_jobs_report.py").read_bytes()
    completed = subprocess.run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=8",
            f"{USER}@{HOST}",
            "sudo",
            "-n",
            "-u",
            "ohana-agent",
            "python3",
            "-",
            JOBS_DATABASE,
            str(days),
        ],
        input=script,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            completed.stderr.decode("utf-8", errors="replace").strip()
            or f"Rapport interrompu avec le code {completed.returncode}"
        )
    return json.loads(completed.stdout.decode("utf-8"))


def print_jobs_report(report: dict) -> None:
    print(f"Jobs distribués sur {report['days']} jour(s), heure de Paris")
    print()
    for day, counts in report["per_day"].items():
        details = ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
        print(f"{day} : {details}")
    print()
    print("Collectes de journaux réussies par source :")
    for name, counts in report["log_sources"].items():
        print(
            f"  {name:<10} {counts.get('collectes', 0)} collecte(s), "
            f"{counts.get('tronquées', 0)} tronquée(s), "
            f"max {counts.get('octets max', 0)} octets"
        )
    print()
    print("Inférences IA par jour : " + (
        ", ".join(f"{day}={count}" for day, count in report["ai_per_day"].items())
        or "aucune"
    ))
    for item in report["ai_per_incident"]:
        print(
            f"  {item['inférences']:>3} × {item.get('cible', item['incident'])}"
            f" (ouvert {item.get('ouvert', '?')}"
            f"{', clos' if item.get('clos') else ', actif' if 'clos' in item else ''})"
        )
    print()
    print("Troncature des collectes par jour (tronquées/collectes) :")
    for day, counts in report["truncated_per_day"].items():
        names = sorted({key.rsplit(" ", 1)[0] for key in counts})
        print(
            f"  {day} : "
            + ", ".join(
                f"{name} {counts.get(f'{name} tronquées', 0)}/"
                f"{counts.get(f'{name} collectes', 0)}"
                for name in names
            )
        )
    print()
    print("Inférences IA par jour et par incident :")
    for day, counts in report["ai_per_day_incident"].items():
        print(
            f"  {day} : "
            + ", ".join(f"{target}={count}" for target, count in counts.items())
        )
    print()
    print("Dernière collecte réussie par source :")
    for name, item in report["latest_collections"].items():
        print(
            f"  {name:<10} {item['le']} tronquée={item['tronquée']} "
            f"octets={item['octets']} lignes={item['lignes analysées']} "
            f"groupes={item['groupes']}"
        )
    print()
    print("Workers : " + ", ".join(
        f"{worker['worker']} {worker['version']} (vu {worker['vu']})"
        for worker in report["workers"]
    ))
    if report["slow_jobs"]:
        print()
        print("Jobs terminés plus de 10 min (ou plus que leur délai) après leur création :")
        for job in report["slow_jobs"]:
            print(
                f"  {job['created_at']} {job['type']} {job['status']} : "
                f"{job['minutes']} min (démarré {job['started_at']}, "
                f"délai {job['timeout_seconds']} s)"
            )
