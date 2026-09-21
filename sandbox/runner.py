from __future__ import annotations

import argparse
import importlib
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
        raise SystemExit(
            f"{root} ne contient pas le paquet attendu src/{package}"
        )

    # Toujours utiliser le checkout local, jamais une version installée.
    sys.path.insert(0, str(source))


def _run_scenario(name: str) -> bool:
    module_name, description = SCENARIOS[name]

    print()
    print("OHANA SANDBOX")
    print(f"Scénario : {name}")
    print(f"But      : {description}")
    print()

    module = importlib.import_module(module_name)

    try:
        module = importlib.import_module(module_name)
        result = module.run()
    except Exception as exc:
        print(f"✗ EXCEPTION : {type(exc).__name__}: {exc}")
        return False

    for label, passed in result["checks"]:
        print(f"{'✓' if passed else '✗'} {label}")

    details = result.get("details") or {}
    if details:
        print()
        for key, value in details.items():
            print(f"{key:<24}: {value}")

    print()
    print(f"RÉSULTAT : {'PASS' if result['passed'] else 'FAIL'}")

    return bool(result["passed"])


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

    _add_python_repo(args.agent, "ohana_agent")

    names = (
        list(SCENARIOS)
        if args.scenario == "all"
        else [args.scenario]
    )

    passed = True

    for name in names:
        passed = _run_scenario(name) and passed

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())