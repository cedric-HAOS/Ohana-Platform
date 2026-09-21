from __future__ import annotations

import json
import re
import subprocess
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PostDeployConfig:
    expected_version: str
    host: str = "192.168.1.10"
    user: str = "ohanna"
    service: str = "ohana-agent"
    agent_bin: str = (
        "/opt/ohana-agent/venv/bin/ohana-agent"
    )
    jobs_db: str = (
        "/var/lib/ohana-agent/distributed-jobs.db"
    )
    admin_port: int = 8765
    journal_minutes: int = 15
    connect_timeout: int = 8
    exercise_logs: bool = False
    exercise_timeout: int = 180

def _exercise_logs(
    config: PostDeployConfig,
) -> dict[str, Any]:
    target = f"{config.user}@{config.host}"

    script = (
        Path(__file__)
        .with_name("remote_exercise_logs.py")
        .read_text(encoding="utf-8")
    )

    completed = subprocess.run(
        [
            "ssh",
            "-o",
            (
                "ConnectTimeout="
                f"{config.connect_timeout}"
            ),
            target,
            "sudo",
            "-n",
            "-u",
            "ohana-agent",
            "python3",
            "-",
            str(config.admin_port),
            config.jobs_db,
            str(config.exercise_timeout),
        ],
        input=script.encode("utf-8"),
        capture_output=True,
        check=False,
    )

    stdout = completed.stdout.decode(
        "utf-8",
        errors="replace",
    ).strip()

    stderr = completed.stderr.decode(
        "utf-8",
        errors="replace",
    ).strip()

    if completed.returncode != 0:
        raise RuntimeError(
            stderr
            or (
                "Exercice journaux terminé "
                f"avec le code {completed.returncode}"
            )
        )

    return json.loads(
        stdout.splitlines()[-1]
    )

def _remote_checker_path() -> Path:
    return Path(__file__).with_name(
        "remote_agent_check.py"
    )


def _remote_result(
    config: PostDeployConfig,
) -> dict[str, Any]:
    try:
        with socket.create_connection(
            (config.host, 22),
            timeout=config.connect_timeout,
        ):
            pass
    except OSError as exc:
        raise RuntimeError(
            f"SSH inaccessible sur {config.host}:22 : "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    
    target = f"{config.user}@{config.host}"

    script = _remote_checker_path().read_text(
        encoding="utf-8"
    )

    completed = subprocess.run(
        [
            "ssh",
            "-o",
            f"ConnectTimeout={config.connect_timeout}",
            target,
            "python3",
            "-",
            config.service,
            config.agent_bin,
            config.jobs_db,
            str(config.admin_port),
            str(config.journal_minutes),
        ],
        input=script.encode("utf-8"),
        capture_output=True,
        check=False,
    )

    stdout = completed.stdout.decode(
        "utf-8",
        errors="replace",
    ).strip()

    stderr = completed.stderr.decode(
        "utf-8",
        errors="replace",
    ).strip()

    if completed.returncode != 0:
        raise RuntimeError(
            stderr
            or (
                "SSH terminé avec le code "
                f"{completed.returncode}"
            )
        )

    output = stdout

    if not output:
        raise RuntimeError(
            "INFRA-01 n'a retourné aucun résultat."
        )

    try:
        return json.loads(
            output.splitlines()[-1]
        )
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Réponse distante invalide : "
            f"{output[-500:]}"
        ) from exc


def _version(text: str) -> str | None:
    match = re.search(
        r"(?<!\d)(\d+\.\d+\.\d+)(?!\d)",
        text,
    )

    return match.group(1) if match else None


def run(
    config: PostDeployConfig,
) -> dict[str, Any]:
    data = _remote_result(config)

    checks: list[tuple[str, bool]] = []

    hostname = str(
        data.get("hostname") or ""
    ).lower()

    checks.append(
        (
            "connexion INFRA-01",
            hostname
            in {
                "infra-01",
                "infra-01.ohana.lan",
            },
        )
    )

    version = data.get("version") or {}

    version_text = (
        f"{version.get('stdout', '')} "
        f"{version.get('stderr', '')}"
    )

    actual_version = _version(version_text)

    checks.append(
        (
            (
                "Ohana-Agent "
                f"{config.expected_version}"
            ),
            (
                version.get("returncode") == 0
                and actual_version
                == config.expected_version
            ),
        )
    )

    service = data.get("service") or {}
    properties = (
        service.get("properties") or {}
    )

    checks.append(
        (
            "service Agent actif",
            (
                service.get("ok") is True
                and properties.get(
                    "ActiveState"
                )
                == "active"
                and properties.get(
                    "SubState"
                )
                == "running"
            ),
        )
    )

    try:
        restart_count = int(
            properties.get(
                "NRestarts",
                "-1",
            )
        )
    except (TypeError, ValueError):
        restart_count = -1

    checks.append(
        (
            "aucun restart automatique",
            restart_count == 0,
        )
    )

    administration = (
        data.get("administration") or {}
    )

    checks.append(
        (
            (
                "port administration "
                f"{config.admin_port}"
            ),
            administration.get("ok") is True,
        )
    )

    jobs = data.get("jobs") or {}

    active = jobs.get("active") or []
    pending = jobs.get("pending") or []

    checks.append(
        (
            "base jobs accessible en lecture",
            jobs.get("ok") is True,
        )
    )

    checks.append(
        (
            "aucun job actif restant",
            (
                jobs.get("ok") is True
                and not active
            ),
        )
    )

    checks.append(
        (
            (
                "aucun résultat terminal "
                "en attente"
            ),
            (
                jobs.get("ok") is True
                and not pending
            ),
        )
    )

    journal = data.get("journal") or {}
    errors = journal.get("errors") or []

    checks.append(
        (
            "journal Agent accessible",
            journal.get("ok") is True,
        )
    )

    checks.append(
        (
            "aucune erreur Agent récente",
            (
                journal.get("ok") is True
                and not errors
            ),
        )
    )

    details = {
        "hôte": data.get("hostname"),
        "version": (
            actual_version
            or version.get("stdout")
            or "?"
        ),
        "service": (
            f"{properties.get('ActiveState', '?')}/"
            f"{properties.get('SubState', '?')}"
        ),
        "NRestarts": restart_count,
        "démarré depuis": (
            properties.get(
                "ExecMainStartTimestamp",
                "?",
            )
        ),
        "jobs actifs": (
            len(active)
            if jobs.get("ok") is True
            else "?"
        ),
        "résultats non traités": (
            len(pending)
            if jobs.get("ok") is True
            else "?"
        ),
        "erreurs journal": len(
            errors
        ),
        "derniers jobs": (
            jobs.get("latest") or []
        ),
        "détail jobs": (
            jobs.get("error")
        ),
        "détail journal": (
            errors
            or journal.get("stderr")
        ),
    }

    if config.exercise_logs:
        try:
            exercise = _exercise_logs(config)
        except Exception as exc:
            checks.append(
                (
                    "exercice réel des journaux",
                    False,
                )
            )
            details[
                "erreur exercice journaux"
            ] = (
                f"{type(exc).__name__}: {exc}"
            )
        else:
            exercised = bool(
                exercise.get("exercised")
            )

            checks.append(
                (
                    "worker disponible pour journaux",
                    exercised,
                )
            )

            if exercised:
                checks.extend(
                    [
                        (
                            "logs.health_check réussi",
                            exercise.get("status")
                            == "SUCCEEDED",
                        ),
                        (
                            "résultat journaux traité",
                            exercise.get(
                                "completion_processed"
                            )
                            == 1,
                        ),
                        (
                            "aucun contrôle journaux résiduel",
                            exercise.get(
                                "active_log_jobs"
                            )
                            == 0,
                        ),
                    ]
                )

            details["job test journaux"] = (
                exercise.get("job_id")
            )
            details["statut test journaux"] = (
                exercise.get("status")
                or exercise.get("reason")
            )
            details[
                "worker test journaux"
            ] = exercise.get("worker_id")

    return {
        "passed": all(
            passed
            for _, passed in checks
        ),
        "checks": checks,
        "details": details,
    }