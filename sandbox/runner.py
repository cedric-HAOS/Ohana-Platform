from __future__ import annotations

import argparse
import importlib
import logging
import sys
from pathlib import Path

from scenarios import SCENARIOS


def _default_repo(name: str) -> Path:
    return Path(__file__).resolve().parents[2] / name


def _add_python_repo(path: Path, package: str) -> None:
    root = path.resolve()
    source = root / "src"

    if not source.is_dir():
        raise SystemExit(f"Dépôt introuvable ou invalide : {root}")

    if not (source / package).is_dir():
        raise SystemExit(f"{root} ne contient pas le paquet attendu src/{package}")

    # Toujours utiliser le checkout local, jamais une version installée.
    sys.path.insert(0, str(source))


def _run_scenario(
    name: str,
    *,
    compact: bool = False,
    options: dict | None = None,
) -> bool:
    module_name, description = (
        (
            "scenarios.exercise_logs",
            "Exercer Agent, Katsuyu et Tsunade depuis les sources locales.",
        )
        if name == "exercise-logs"
        else (
            "integration.full_stack",
            "Worker HTTPS, IA réelle et rendu Vision locaux.",
        )
        if name == "full-stack"
        else SCENARIOS[name]
    )

    if not compact:
        print()
        print("OHANA SANDBOX")
        print(f"Scénario : {name}")
        print(f"But      : {description}")
        print()

    previous_disable = logging.root.manager.disable

    if compact:
        # Évite notamment les messages attendus de probe-error.
        logging.disable(logging.CRITICAL)

    try:
        module = importlib.import_module(module_name)
        result = module.run(**(options or {}))
    except Exception as exc:
        if compact:
            print(f"✗ {name:<28} FAIL")
        else:
            print(f"✗ EXCEPTION : {type(exc).__name__}: {exc}")
        return False
    finally:
        if compact:
            logging.disable(previous_disable)

    passed = bool(result["passed"])

    if compact:
        print(f"{'✓' if passed else '✗'} {name:<28} {'PASS' if passed else 'FAIL'}")
        return passed

    for label, check_passed in result["checks"]:
        print(f"{'✓' if check_passed else '✗'} {label}")

    details = result.get("details") or {}

    if details:
        print()

        for key, value in details.items():
            print(f"{key:<24}: {value}")

    print()
    print(f"RÉSULTAT : {'PASS' if passed else 'FAIL'}")

    return passed


def _run_post_deploy(
    args: argparse.Namespace,
) -> bool:
    from production.post_deploy import (
        PostDeployConfig,
        run,
    )

    print()
    print("OHANA POST-DEPLOY CHECK")
    print(f"Cible    : {args.user}@{args.host}")
    print(f"Composant: Ohana-Agent {args.version}")
    print()

    try:
        result = run(
            PostDeployConfig(
                expected_version=args.version,
                host=args.host,
                user=args.user,
                journal_minutes=(args.journal_minutes),
                exercise_logs=args.exercise_logs,
                exercise_timeout=args.exercise_timeout,
            )
        )
    except Exception as exc:
        print(f"✗ EXCEPTION : {type(exc).__name__}: {exc}")
        return False

    for label, passed in result["checks"]:
        print(f"{'✓' if passed else '✗'} {label}")

    details = result.get("details") or {}

    if details:
        print()

        for key, value in details.items():
            if value in (
                None,
                "",
                [],
                {},
            ):
                continue

            print(f"{key:<24}: {value}")

    passed = bool(result["passed"])

    print()
    print(f"DÉPLOIEMENT : {'PASS' if passed else 'À VÉRIFIER'}")

    return passed


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bac à sable d'intégration de l'écosystème Ohana."
    )
    parser.add_argument(
        "--agent",
        type=Path,
        default=_default_repo("Ohana-Agent"),
        help="Chemin du checkout local Ohana-Agent.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "list",
        help="Lister les scénarios disponibles.",
    )

    run_parser = subparsers.add_parser(
        "run",
        help="Exécuter un scénario.",
    )
    run_parser.add_argument(
        "scenario",
        nargs="?",
        choices=[*SCENARIOS, "all"],
        help="Nom du scénario, ou 'all'.",
    )
    run_parser.add_argument(
        "--exercise-logs",
        action="store_true",
        help="Exercer les sources locales Agent/Katsuyu, sans déploiement.",
    )
    run_parser.add_argument(
        "--katsuyu", type=Path, default=_default_repo("Ohana-Katsuyu")
    )
    run_parser.add_argument(
        "--logs-file",
        type=Path,
        help="Rejouer un journal UTF-8 local au lieu des cas intégrés.",
    )
    run_parser.add_argument(
        "--window-end",
        help="Fin de fenêtre ISO 8601 avec fuseau pour un journal historique.",
    )
    run_parser.add_argument(
        "--full-stack",
        action="store_true",
        help="Exercer le worker HTTPS, l'IA réelle et Vision dans Chromium.",
    )
    run_parser.add_argument(
        "--vision", type=Path, default=_default_repo("Ohana-Vision")
    )
    run_parser.add_argument("--ai-runtime", type=Path)
    run_parser.add_argument("--ai-model", type=Path)
    run_parser.add_argument("--ai-model-sha256")
    run_parser.add_argument("--ai-context-size", type=int, default=16384)
    run_parser.add_argument("--stack-timeout", type=int, default=900)
    run_parser.add_argument(
        "--report-dir", type=Path, default=Path(__file__).parent / "runs"
    )

    post_deploy = subparsers.add_parser(
        "post-deploy",
        help=("Contrôler un déploiement réel en lecture seule."),
    )

    post_deploy.add_argument(
        "component",
        choices=["agent"],
        help="Composant à contrôler.",
    )

    post_deploy.add_argument(
        "version",
        help=("Version attendue, par exemple 1.29.14."),
    )

    post_deploy.add_argument(
        "--host",
        default="192.168.1.10",
        help="Hôte SSH cible.",
    )

    post_deploy.add_argument(
        "--user",
        default="ohanna",
        help="Utilisateur SSH.",
    )

    post_deploy.add_argument(
        "--journal-minutes",
        type=int,
        default=15,
        help=("Fenêtre du journal à contrôler."),
    )

    post_deploy.add_argument(
        "--exercise-logs",
        action="store_true",
        help=("Déclencher un contrôle réel logs.health_check après la recette."),
    )

    post_deploy.add_argument(
        "--exercise-timeout",
        type=int,
        default=180,
        help=("Délai maximal du contrôle réel des journaux en secondes."),
    )

    args = parser.parse_args()
    if args.command == "run":
        if not args.scenario and not args.exercise_logs and not args.full_stack:
            parser.error("run exige un scénario, --exercise-logs ou --full-stack")
        if (args.logs_file or args.window_end) and not args.exercise_logs:
            parser.error("--logs-file et --window-end exigent --exercise-logs")
        if args.stack_timeout < 30:
            parser.error("--stack-timeout doit être >= 30 secondes")
    return args


def main() -> int:
    args = _parse_args()

    if args.command == "list":
        print("Scénarios Ohana Sandbox :")

        for name, (_, description) in SCENARIOS.items():
            print(f"  {name:<28} {description}")

        return 0

    if args.command == "post-deploy":
        passed = _run_post_deploy(args)

        return 0 if passed else 1

    _add_python_repo(
        args.agent,
        "ohana_agent",
    )

    exercise_passed = True
    if args.exercise_logs or args.full_stack:
        katsuyu_root = args.katsuyu.resolve()
        if not (katsuyu_root / "ohana_katsuyu").is_dir():
            raise SystemExit(f"Checkout Katsuyu invalide : {katsuyu_root}")
        sys.path.insert(0, str(katsuyu_root))
    if args.full_stack:
        _add_python_repo(args.vision, "ohana_vision")
        exercise_passed = _run_scenario("full-stack", options={"args": args})
    if args.exercise_logs:
        logs_passed = _run_scenario(
            "exercise-logs",
            options={
                "logs_file": args.logs_file,
                "window_end": args.window_end,
            },
        )
        exercise_passed = exercise_passed and logs_passed
    if not args.scenario:
        return 0 if exercise_passed else 1

    names = list(SCENARIOS) if args.scenario == "all" else [args.scenario]

    if args.scenario == "all":
        print()
        print("OHANA SANDBOX")
        print()

        passed = True
        passed_count = 0

        for name in names:
            scenario_passed = _run_scenario(
                name,
                compact=True,
            )

            if scenario_passed:
                passed_count += 1

            passed = scenario_passed and passed

        print()
        print(
            f"{passed_count}/{len(names)} scénarios {'PASS' if passed else '— ÉCHEC'}"
        )

    else:
        passed = _run_scenario(
            names[0],
            compact=False,
        )

    return 0 if passed and exercise_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
