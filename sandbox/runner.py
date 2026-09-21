from __future__ import annotations

import argparse
import importlib
import sys
import logging
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
        raise SystemExit(
            f"{root} ne contient pas le paquet attendu src/{package}"
        )

    # Toujours utiliser le checkout local, jamais une version installée.
    sys.path.insert(0, str(source))


def _run_scenario(
    name: str,
    *,
    compact: bool = False,
) -> bool:
    module_name, description = SCENARIOS[name]

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
        result = module.run()
    except Exception as exc:
        if compact:
            print(f"✗ {name:<28} FAIL")
        else:
            print(
                f"✗ EXCEPTION : "
                f"{type(exc).__name__}: {exc}"
            )
        return False
    finally:
        if compact:
            logging.disable(previous_disable)

    passed = bool(result["passed"])

    if compact:
        print(
            f"{'✓' if passed else '✗'} "
            f"{name:<28} "
            f"{'PASS' if passed else 'FAIL'}"
        )
        return passed

    for label, check_passed in result["checks"]:
        print(
            f"{'✓' if check_passed else '✗'} "
            f"{label}"
        )

    details = result.get("details") or {}

    if details:
        print()

        for key, value in details.items():
            print(f"{key:<24}: {value}")

    print()
    print(
        f"RÉSULTAT : "
        f"{'PASS' if passed else 'FAIL'}"
    )

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
        choices=[*SCENARIOS, "all"],
        help="Nom du scénario, ou 'all'.",
    )

    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    if args.command == "list":
        print("Scénarios Ohana Sandbox :")

        for name, (_, description) in SCENARIOS.items():
            print(f"  {name:<28} {description}")

        return 0

    _add_python_repo(
        args.agent,
        "ohana_agent",
    )

    names = (
        list(SCENARIOS)
        if args.scenario == "all"
        else [args.scenario]
    )

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
            f"{passed_count}/{len(names)} scénarios "
            f"{'PASS' if passed else '— ÉCHEC'}"
        )

    else:
        passed = _run_scenario(
            names[0],
            compact=False,
        )

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())