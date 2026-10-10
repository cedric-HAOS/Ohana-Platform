#!/usr/bin/env python3
"""Interactive, verified release workflow for the Ohana repositories."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG_DIRECTORY = ROOT / ".release-logs"
ACTIVE_LOG: Path | None = None
PROGRESS_WIDTH = 0
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


@dataclass(frozen=True)
class Repository:
    key: str
    directory: str
    github: str
    kind: str

    @property
    def path(self) -> Path:
        return ROOT / self.directory


@dataclass(frozen=True)
class GitState:
    status: str
    ahead: int
    behind: int

    @property
    def has_local_changes(self) -> bool:
        return bool(self.status) or self.ahead > 0


# Platform precedes Installer because a Platform release synchronizes the two
# manifest copies and their Installer expectations.
REPOSITORIES = (
    Repository("agent", "Ohana-Agent", "cedric-HAOS/Ohana-Agent", "python"),
    Repository("vision", "Ohana-Vision", "cedric-HAOS/Ohana-Vision", "python"),
    Repository("katsuyu", "Ohana-Katsuyu", "cedric-HAOS/Ohana-Katsuyu", "python"),
    Repository("shizune", "Ohana-Shizune", "cedric-HAOS/Ohana-Shizune", "static"),
    Repository("platform", "Ohana-Platform", "cedric-HAOS/Ohana-Platform", "platform"),
    Repository("installer", "Ohana-Installer", "cedric-HAOS/Ohana-Installer", "python"),
)


class ReleaseError(RuntimeError):
    pass


def write_utf8(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def begin_log(repository: Repository) -> Path:
    global ACTIVE_LOG
    LOG_DIRECTORY.mkdir(exist_ok=True)
    timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    ACTIVE_LOG = LOG_DIRECTORY / f"{timestamp}-{repository.key}.log"
    write_utf8(ACTIVE_LOG, f"Release log for {repository.directory}\n")
    return ACTIVE_LOG


def append_log(command: list[str], result: subprocess.CompletedProcess[str]) -> None:
    if ACTIVE_LOG is None:
        return
    with ACTIVE_LOG.open("a", encoding="utf-8") as stream:
        stream.write(f"\n> {' '.join(command)}\n")
        if result.stdout:
            stream.write(result.stdout)
            if not result.stdout.endswith("\n"):
                stream.write("\n")
        if result.stderr:
            stream.write(result.stderr)
            if not result.stderr.endswith("\n"):
                stream.write("\n")
        stream.write(f"[exit={result.returncode}]\n")


def execute(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
    )
    append_log(command, result)
    return result


def run(command: list[str], cwd: Path, *, capture: bool = False) -> str:
    result = execute(command, cwd)
    if result.returncode:
        log_hint = f" Consultez {ACTIVE_LOG}." if ACTIVE_LOG else ""
        raise ReleaseError(f"Commande échouée ({result.returncode}).{log_hint}")
    return result.stdout.strip() if capture else ""


def progress(repository: Repository, percent: int, message: str) -> None:
    global PROGRESS_WIDTH
    line = f"[{repository.directory}] {percent:3d}% - {message}"
    width = max(PROGRESS_WIDTH, len(line))
    if percent >= 100:
        print(f"\r{line.ljust(width)}")
        PROGRESS_WIDTH = 0
        return
    print(f"\r{line.ljust(width)}", end="", flush=True)
    PROGRESS_WIDTH = width


def clear_progress_line() -> None:
    global PROGRESS_WIDTH
    if PROGRESS_WIDTH:
        print(f"\r{' ' * PROGRESS_WIDTH}\r", end="", flush=True)
        PROGRESS_WIDTH = 0


def ask_yes_no(question: str) -> bool:
    clear_progress_line()
    while True:
        answer = input(f"{question} [o/N] ").strip().lower()
        if answer in {"o", "oui", "y", "yes"}:
            return True
        if answer in {"", "n", "non", "no"}:
            return False
        print("Réponse attendue : oui ou non.")


def parse_version(value: str) -> tuple[int, int, int]:
    match = SEMVER.fullmatch(value)
    if not match:
        raise ReleaseError(f"Version invalide : {value!r}; format attendu X.Y.Z")
    return tuple(int(part) for part in match.groups())


def next_patch(version: str) -> str:
    major, minor, patch = parse_version(version)
    return f"{major}.{minor}.{patch + 1}"


def local_version(repository: Repository) -> str:
    if repository.kind == "static":
        data = json.loads(
            (repository.path / "Shizune" / "PWA" / "version.json").read_text(
                encoding="utf-8"
            )
        )
        return str(data["version"])
    if repository.kind == "platform":
        text = (repository.path / "release-manifest.yaml").read_text(encoding="utf-8")
        match = re.search(
            r"(?ms)^platform:\s*\n\s+name:.*?\n\s+version:\s*[\"']?([^\"'\s]+)",
            text,
        )
        if match:
            return match.group(1)
        raise ReleaseError("Version Platform introuvable dans release-manifest.yaml")
    data = tomllib.loads(
        (repository.path / "pyproject.toml").read_text(encoding="utf-8")
    )
    return str(data["project"]["version"])


def github_version(repository: Repository) -> str | None:
    result = execute(
        [
            "gh",
            "api",
            f"repos/{repository.github}/releases/latest",
            "--jq",
            ".tag_name",
        ],
        ROOT,
    )
    if result.returncode and "404" not in result.stderr:
        raise ReleaseError(
            (result.stderr.strip() or "Impossible de lire la release GitHub")
            + (f" Consultez {ACTIVE_LOG}." if ACTIVE_LOG else "")
        )
    output = result.stdout.strip()
    return output.removeprefix("v") if output and output != "null" else None


def python_executable(repository: Repository) -> str:
    candidates = (
        repository.path / ".venv" / "Scripts" / "python.exe",
        repository.path / ".venv-release" / "Scripts" / "python.exe",
    )
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return shutil.which("python") or sys.executable


def inspect_git_state(repository: Repository) -> GitState:
    progress(repository, 2, "synchronisation des références GitHub")
    run(["git", "fetch", "origin", "--prune"], repository.path)
    branch = run(["git", "branch", "--show-current"], repository.path, capture=True)
    if branch != "main":
        raise ReleaseError(
            f"{repository.directory}: branche courante {branch!r}, main requise"
        )
    counts = run(
        ["git", "rev-list", "--left-right", "--count", "origin/main...HEAD"],
        repository.path,
        capture=True,
    ).split()
    if len(counts) != 2:
        raise ReleaseError(f"{repository.directory}: état Git impossible à déterminer")
    behind, ahead = (int(value) for value in counts)
    status = run(["git", "status", "--porcelain"], repository.path, capture=True)
    state = GitState(status=status, ahead=ahead, behind=behind)
    if behind:
        relation = "divergent" if ahead else "en retard"
        raise ReleaseError(
            f"{repository.directory}: dépôt {relation} de {behind} commit(s); "
            "synchronisez-le manuellement avant une release"
        )
    return state


def request_new_version(
    repository: Repository, current: str, remote: str | None
) -> str:
    clear_progress_line()
    print(f"  Version locale actuelle : {current}")
    print(f"  Dernière release GitHub : {remote or 'aucune'}")
    value = input("  Nouvelle version à appliquer (X.Y.Z) : ").strip()
    parsed = parse_version(value)
    current_parsed = parse_version(current)
    if parsed < current_parsed:
        raise ReleaseError(
            f"La nouvelle version ne peut pas être inférieure à {current}"
        )
    if remote is not None and parsed <= parse_version(remote):
        raise ReleaseError(
            f"La nouvelle version doit être supérieure à GitHub {remote}"
        )
    if parsed == current_parsed and (
        remote is None or current_parsed <= parse_version(remote)
    ):
        raise ReleaseError(
            "La version locale n’est pas déjà préparée au-dessus de GitHub; "
            "choisissez une version supérieure"
        )
    tag = f"v{value}"
    local_tag = execute(
        ["git", "show-ref", "--verify", "--quiet", f"refs/tags/{tag}"],
        repository.path,
    )
    if local_tag.returncode == 0:
        raise ReleaseError(f"Le tag local {tag} existe déjà")
    if local_tag.returncode not in {0, 1}:
        raise ReleaseError(f"Impossible de vérifier le tag local {tag}")
    remote_tag = execute(
        ["git", "ls-remote", "--exit-code", "--tags", "origin", f"refs/tags/{tag}"],
        repository.path,
    )
    if remote_tag.returncode == 0:
        raise ReleaseError(f"Le tag distant {tag} existe déjà")
    if remote_tag.returncode not in {0, 2}:
        raise ReleaseError(f"Impossible de vérifier le tag distant {tag}")
    return value


def replace_literal(
    path: Path,
    old: str,
    new: str,
    *,
    expected: int,
    label: str,
) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise ReleaseError(
            f"{label}: {count} occurrence(s) trouvée(s), {expected} attendue(s) dans {path}"
        )
    write_utf8(path, text.replace(old, new))


def replace_optional(path: Path, old: str, new: str, *, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count > 1:
        raise ReleaseError(f"{label}: plusieurs occurrences ambiguës dans {path}")
    if count == 1:
        write_utf8(path, text.replace(old, new))


def update_platform_version(repository: Repository, old: str, new: str) -> None:
    manifest_path = repository.path / "release-manifest.yaml"
    catalog_path = repository.path / "release-catalog.yaml"
    manifest = manifest_path.read_text(encoding="utf-8")
    manifest_token = f'platform:\n  name: Ohana\n  version: "{old}"'
    if manifest.count(manifest_token) != 1:
        raise ReleaseError(
            "Platform: version courante ambiguë dans release-manifest.yaml"
        )
    manifest = manifest.replace(
        manifest_token,
        f'platform:\n  name: Ohana\n  version: "{new}"',
    )
    write_utf8(manifest_path, manifest)

    catalog = catalog_path.read_text(encoding="utf-8")
    header_old = (
        f'platform:\n  name: Ohana\n  version: "{old}"\n\n'
        f'default_platform_version: "{old}"'
    )
    header_new = (
        f'platform:\n  name: Ohana\n  version: "{new}"\n\n'
        f'default_platform_version: "{new}"'
    )
    if catalog.count(header_old) != 1:
        raise ReleaseError("Platform: en-tête courant ambigu dans release-catalog.yaml")
    catalog = catalog.replace(header_old, header_new)
    block_match = re.search(
        r"(?ms)^(  - platform_version:.*?)(?=^  - platform_version:|\Z)",
        catalog,
    )
    if not block_match:
        raise ReleaseError("Platform: composition recommandée introuvable")
    current_block = block_match.group(1).rstrip()
    if (
        f'platform_version: "{old}"' not in current_block
        or f"release_tag: v{old}" not in current_block
    ):
        raise ReleaseError(
            "Platform: la première composition ne correspond pas à la version courante"
        )
    if current_block.count("status: recommended") != 1:
        raise ReleaseError("Platform: statut recommended ambigu")
    new_block = current_block.replace(
        f'platform_version: "{old}"', f'platform_version: "{new}"', 1
    ).replace(f"release_tag: v{old}", f"release_tag: v{new}", 1)
    component_versions = manifest_component_versions(manifest)
    for component, component_version in component_versions.items():
        pattern = rf'(?m)^(    {component}_version:) "[^"]+"$'
        new_block, count = re.subn(
            pattern,
            rf'\1 "{component_version}"',
            new_block,
            count=1,
        )
        if count != 1:
            raise ReleaseError(
                f"Platform: version {component} absente de la composition recommandée"
            )
    retained_block = current_block.replace(
        "status: recommended", "status: supported", 1
    )
    # Keep the blank line that separated the retained block from the next one.
    trailing = block_match.group(1)[len(current_block) :] or "\n"
    replacement = f"{new_block}\n\n{retained_block}{trailing}"
    catalog = (
        catalog[: block_match.start()] + replacement + catalog[block_match.end() :]
    )
    write_utf8(catalog_path, catalog)


def normalize_version_file_line_endings(repository: Repository) -> None:
    paths: dict[str, tuple[str, ...]] = {
        "agent": (
            "pyproject.toml",
            "tests/test_package_metadata.py",
        ),
        "vision": ("pyproject.toml",),
        "installer": (
            "pyproject.toml",
            "src/ohana_installer/version.py",
            "tests/test_interactive.py",
            "tests/test_update.py",
        ),
        "katsuyu": (
            "pyproject.toml",
            "ohana_katsuyu/__init__.py",
            "tests/test_package.py",
            "tests/test_setup.py",
            "tests/test_updates.py",
        ),
        "shizune": ("Shizune/PWA/version.json",),
        "platform": (
            "release-manifest.yaml",
            "release-catalog.yaml",
        ),
    }

    for relative in paths[repository.key]:
        path = repository.path / relative
        content = path.read_bytes()
        normalized = content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")

        if normalized != content:
            path.write_bytes(normalized)


def update_version_references(repository: Repository, old: str, new: str) -> None:
    progress(repository, 18, "propagation contrôlée du numéro de version")

    if repository.key == "agent":
        replace_literal(
            repository.path / "pyproject.toml",
            f'version = "{old}"',
            f'version = "{new}"',
            expected=1,
            label="Agent pyproject",
        )
        replace_literal(
            repository.path / "tests" / "test_package_metadata.py",
            f'assert project["version"] == "{old}"',
            f'assert project["version"] == "{new}"',
            expected=1,
            label="Agent test metadata",
        )

    elif repository.key == "vision":
        replace_literal(
            repository.path / "pyproject.toml",
            f'version = "{old}"',
            f'version = "{new}"',
            expected=1,
            label="Vision pyproject",
        )

    elif repository.key == "installer":
        replace_literal(
            repository.path / "pyproject.toml",
            f'version = "{old}"',
            f'version = "{new}"',
            expected=1,
            label="Installer pyproject",
        )
        replace_literal(
            repository.path / "src" / "ohana_installer" / "version.py",
            f'__version__ = "{old}"',
            f'__version__ = "{new}"',
            expected=1,
            label="Installer runtime version",
        )
        replace_literal(
            repository.path / "tests" / "test_interactive.py",
            f"Ohana Installer {old}",
            f"Ohana Installer {new}",
            expected=2,
            label="Installer display tests",
        )
        # Update tests now derive candidate versions from runtime __version__.
        # They no longer contain eight literals for the next patch version.

    elif repository.key == "katsuyu":
        replace_literal(
            repository.path / "pyproject.toml",
            f'version = "{old}"',
            f'version = "{new}"',
            expected=1,
            label="Katsuyu pyproject",
        )
        replace_literal(
            repository.path / "ohana_katsuyu" / "__init__.py",
            f'__version__ = "{old}"',
            f'__version__ = "{new}"',
            expected=1,
            label="Katsuyu runtime version",
        )

        for relative, token in (
            (
                "tests/test_package.py",
                f'assert project["version"] == "{old}"',
            ),
            (
                "tests/test_setup.py",
                f'["worker_version"] == "{old}"',
            ),
            (
                "tests/test_updates.py",
                f'== "Ohana-Katsuyu/{old}"',
            ),
        ):
            replace_literal(
                repository.path / relative,
                token,
                token.replace(old, new),
                expected=1,
                label=f"Katsuyu {relative}",
            )

    elif repository.key == "shizune":
        replace_literal(
            repository.path / "Shizune" / "PWA" / "version.json",
            f'"version": "{old}"',
            f'"version": "{new}"',
            expected=1,
            label="Shizune version.json",
        )

    elif repository.key == "platform":
        update_platform_version(repository, old, new)
        sync_platform_to_installer(repository)

    else:
        raise ReleaseError(f"Aucune règle de version pour {repository.key}")

    if local_version(repository) != new:
        raise ReleaseError(
            f"{repository.directory}: la version effective n’est pas {new}"
        )


def manifest_component_versions(text: str) -> dict[str, str]:
    versions: dict[str, str] = {}
    for component in ("agent", "vision", "shizune"):
        match = re.search(
            rf"(?ms)^  {component}:\s*\n.*?^    version:\s*\"([^\"]+)\"",
            text,
        )
        if not match:
            raise ReleaseError(f"Composant {component} introuvable dans le manifeste")
        versions[component] = match.group(1)
    return versions


def propagate_component_to_platform(
    repository: Repository,
    new_version: str,
    platform_path: Path | None = None,
) -> None:
    if repository.key not in {"agent", "vision", "shizune"}:
        return

    root = platform_path or ROOT / "Ohana-Platform"
    manifest_path = root / "release-manifest.yaml"
    manifest = manifest_path.read_text(encoding="utf-8")

    section_match = re.search(
        rf"(?ms)"
        rf"(^  {repository.key}:\s*\n.*?)"
        rf"(?=^  [a-z][a-z0-9-]*:\s*\n|^compatibility:|\Z)",
        manifest,
    )

    if not section_match:
        raise ReleaseError(
            f"Platform: composant {repository.key} "
            "introuvable dans release-manifest.yaml"
        )

    section = section_match.group(1)

    version_match = re.search(
        r'(?m)^    version:\s*"([^"]+)"\s*$',
        section,
    )

    if not version_match:
        raise ReleaseError(
            f"Platform: version du composant {repository.key} introuvable"
        )

    current_version = version_match.group(1)

    if current_version == new_version:
        return

    package_prefix = {
        "agent": "ohana_agent-",
        "vision": "ohana_vision-",
        "shizune": "shizune-pwa-",
    }[repository.key]

    replacements = (
        (
            f'    version: "{current_version}"',
            f'    version: "{new_version}"',
            "version",
        ),
        (
            f"    release_tag: v{current_version}",
            f"    release_tag: v{new_version}",
            "release_tag",
        ),
        (
            f"{package_prefix}{current_version}",
            f"{package_prefix}{new_version}",
            "package filename",
        ),
    )

    updated_section = section

    for old_token, new_token, label in replacements:
        count = updated_section.count(old_token)

        if count != 1:
            raise ReleaseError(
                f"Platform: référence {label} ambiguë pour "
                f"{repository.key}: {count} occurrence(s)"
            )

        updated_section = updated_section.replace(
            old_token,
            new_token,
            1,
        )

    updated_manifest = (
        manifest[: section_match.start()]
        + updated_section
        + manifest[section_match.end() :]
    )

    write_utf8(
        manifest_path,
        updated_manifest,
    )


def sync_platform_to_installer(
    platform: Repository,
    installer_path: Path | None = None,
) -> None:
    installer = installer_path or ROOT / "Ohana-Installer"
    old_manifest = (installer / "config" / "release-manifest.yaml").read_text(
        encoding="utf-8"
    )
    old_platform = re.search(
        r"(?ms)^platform:\s*\n\s+name:.*?\n\s+version:\s*\"([^\"]+)\"",
        old_manifest,
    )
    if not old_platform:
        raise ReleaseError("Version Platform miroir introuvable dans Installer")
    old_components = manifest_component_versions(old_manifest)
    new_manifest_path = platform.path / "release-manifest.yaml"
    new_manifest = new_manifest_path.read_text(encoding="utf-8")
    new_components = manifest_component_versions(new_manifest)
    new_platform = local_version(platform)
    shutil.copy2(new_manifest_path, installer / "config" / "release-manifest.yaml")
    shutil.copy2(
        platform.path / "release-catalog.yaml",
        installer / "config" / "release-catalog.yaml",
    )
    replace_literal(
        installer / "tests" / "test_manifest.py",
        f'assert manifest.platform_version == "{old_platform.group(1)}"',
        f'assert manifest.platform_version == "{new_platform}"',
        expected=1,
        label="Installer manifest platform expectation",
    )
    replace_literal(
        installer / "tests" / "test_release_catalog.py",
        f'catalog.platform_version == "{old_platform.group(1)}"',
        f'catalog.platform_version == "{new_platform}"',
        expected=1,
        label="Installer catalog platform version",
    )
    replace_literal(
        installer / "tests" / "test_release_catalog.py",
        f'catalog.default_platform_version == "{old_platform.group(1)}"',
        f'catalog.default_platform_version == "{new_platform}"',
        expected=1,
        label="Installer catalog default version",
    )
    for component, old_version in old_components.items():
        new_version = new_components[component]
        if old_version == new_version:
            continue
        manifest_test = installer / "tests" / "test_manifest.py"
        replace_literal(
            manifest_test,
            f'assert {component}.version == "{old_version}"',
            f'assert {component}.version == "{new_version}"',
            expected=1,
            label=f"Installer {component} manifest version",
        )
        filename_prefix = {
            "agent": "ohana_agent-",
            "vision": "ohana_vision-",
            "shizune": "shizune-pwa-",
        }[component]
        replace_literal(
            manifest_test,
            f"{filename_prefix}{old_version}",
            f"{filename_prefix}{new_version}",
            expected=1,
            label=f"Installer {component} package filename",
        )
        if component != "shizune":
            replace_literal(
                manifest_test,
                f'assert {component}.release_tag == "v{old_version}"',
                f'assert {component}.release_tag == "v{new_version}"',
                expected=1,
                label=f"Installer {component} release tag",
            )
        replace_literal(
            installer / "tests" / "test_release_catalog.py",
            f'catalog.releases[0].{component}_version == "{old_version}"',
            f'catalog.releases[0].{component}_version == "{new_version}"',
            expected=1,
            label=f"Installer catalog {component} version",
        )


def run_checks(repository: Repository) -> None:
    progress(repository, 24, "contrôle du diff")
    run(["git", "diff", "--check"], repository.path)

    if repository.kind == "platform":
        progress(
            repository,
            30,
            "validation YAML et cohérence Platform/Installer",
        )

        installer = next(item for item in REPOSITORIES if item.key == "installer")
        python = python_executable(installer)

        run(
            [
                python,
                "-m",
                "pytest",
                "-q",
                "--basetemp=.pytest_tmp",
                "tests/test_manifest.py",
                "tests/test_release_catalog.py",
            ],
            installer.path,
        )

        progress(
            repository,
            78,
            "validation Platform terminée",
        )
        return

    if repository.kind == "static":
        progress(
            repository,
            35,
            "validation de la PWA",
        )

        json.loads(
            (repository.path / "Shizune" / "PWA" / "version.json").read_text(
                encoding="utf-8"
            )
        )

        node = shutil.which("node")

        if node:
            run(
                [
                    node,
                    "--check",
                    "Shizune/PWA/app.js",
                ],
                repository.path,
            )
            run(
                [
                    node,
                    "--check",
                    "Shizune/PWA/sw.js",
                ],
                repository.path,
            )

        progress(
            repository,
            78,
            "validation PWA terminée",
        )
        return

    python = python_executable(repository)

    progress(
        repository,
        28,
        "formatage Ruff",
    )
    run(
        [
            python,
            "-m",
            "ruff",
            "format",
            ".",
        ],
        repository.path,
    )

    progress(
        repository,
        38,
        "corrections Ruff",
    )
    run(
        [
            python,
            "-m",
            "ruff",
            "check",
            "--fix",
            ".",
        ],
        repository.path,
    )

    progress(
        repository,
        46,
        "normalisation finale du format",
    )
    run(
        [
            python,
            "-m",
            "ruff",
            "format",
            ".",
        ],
        repository.path,
    )

    progress(
        repository,
        52,
        "contrôle Ruff sans correction",
    )
    run(
        [
            python,
            "-m",
            "ruff",
            "check",
            ".",
        ],
        repository.path,
    )
    run(
        [
            python,
            "-m",
            "ruff",
            "format",
            "--check",
            ".",
        ],
        repository.path,
    )

    progress(
        repository,
        62,
        "exécution de pytest",
    )
    run(
        [
            python,
            "-m",
            "pytest",
            "-q",
            "--basetemp=.pytest_tmp",
        ],
        repository.path,
    )

    if repository.key == "agent":
        progress(
            repository,
            72,
            "construction propre du package Agent",
        )
        run(
            [
                python,
                "scripts/build_release.py",
            ],
            repository.path,
        )

        progress(
            repository,
            78,
            "validation de l’installation propre d’Agent",
        )
        run(
            [
                python,
                "scripts/test_clean_install.py",
            ],
            repository.path,
        )

        return

    progress(
        repository,
        74,
        "construction des packages",
    )
    run(
        [
            python,
            "-m",
            "build",
        ],
        repository.path,
    )

    if repository.key == "katsuyu":
        progress(
            repository,
            78,
            "construction de KatsuyuSetup.exe",
        )
        run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(repository.path / "scripts" / "build_windows.ps1"),
            ],
            repository.path,
        )


def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def prepare_assets(repository: Repository, version: str) -> list[Path]:
    progress(repository, 82, "préparation des assets et SHA256SUMS")
    dist = repository.path / "dist"
    dist.mkdir(exist_ok=True)
    if repository.kind == "static":
        archive = dist / f"shizune-pwa-{version}.tar.gz"
        run(["tar", "-czf", str(archive), "-C", "Shizune/PWA", "."], repository.path)
        assets = [archive]
    elif repository.kind == "platform":
        assets = []
        for filename in ("release-manifest.yaml", "release-catalog.yaml"):
            destination = dist / filename
            shutil.copy2(repository.path / filename, destination)
            assets.append(destination)
    elif repository.key == "katsuyu":
        setup = dist / "KatsuyuSetup.exe"
        if not setup.is_file():
            raise ReleaseError("katsuyu: dist/KatsuyuSetup.exe est absent")
        assets = [setup]
    else:
        assets = sorted(
            path for path in dist.iterdir() if path.is_file() and version in path.name
        )
        if repository.key == "agent":
            examples = sorted((repository.path / "config").rglob("*.example.yaml"))
            names = [example.name for example in examples]
            if len(names) != len(set(names)):
                raise ReleaseError(
                    "agent: deux fichiers *.example.yaml ont le même nom"
                )
            for example in examples:
                destination = dist / example.name
                shutil.copy2(example, destination)
                assets.append(destination)
        elif repository.key == "vision":
            example = repository.path / "config" / "vision.example.yaml"
            shutil.copy2(example, dist / example.name)
            assets.append(dist / example.name)
    if not assets:
        raise ReleaseError(f"{repository.key}: aucun asset trouvé dans dist")
    validate_asset_contract(repository, version, assets)
    sums = dist / "SHA256SUMS"
    write_utf8(
        sums,
        "".join(f"{sha256sum(path)}  {path.name}\n" for path in assets),
    )
    return assets + [sums]


def validate_asset_contract(
    repository: Repository, version: str, assets: list[Path]
) -> None:
    names = [path.name for path in assets]
    if len(names) != len(set(names)):
        raise ReleaseError(f"{repository.key}: noms d’assets dupliqués")
    if repository.kind == "static":
        expected = {f"shizune-pwa-{version}.tar.gz"}
    elif repository.kind == "platform":
        expected = {"release-manifest.yaml", "release-catalog.yaml"}
    elif repository.key == "katsuyu":
        expected = {"KatsuyuSetup.exe"}
    else:
        wheels = [name for name in names if version in name and name.endswith(".whl")]
        sdists = [
            name for name in names if version in name and name.endswith(".tar.gz")
        ]
        if len(wheels) != 1 or len(sdists) != 1:
            raise ReleaseError(
                f"{repository.key}: un wheel et un sdist de la version {version} sont requis"
            )
        expected = {wheels[0], sdists[0]}
        if repository.key == "agent":
            expected.update(
                path.name
                for path in (repository.path / "config").rglob("*.example.yaml")
            )
        elif repository.key == "vision":
            expected.add("vision.example.yaml")
    actual = set(names)
    if actual != expected:
        missing = ", ".join(sorted(expected - actual)) or "aucun"
        unexpected = ", ".join(sorted(actual - expected)) or "aucun"
        raise ReleaseError(
            f"{repository.key}: contrat d’assets invalide; "
            f"manquants={missing}; inattendus={unexpected}"
        )


def commit_release(repository: Repository, version: str) -> None:
    progress(repository, 86, "création du commit de release")
    run(["git", "diff", "--check"], repository.path)
    run(["git", "add", "--all"], repository.path)
    if execute(["git", "diff", "--cached", "--quiet"], repository.path).returncode == 0:
        raise ReleaseError(f"{repository.directory}: aucun changement à committer")
    message = (
        f"release: compose Platform {version}"
        if repository.key == "platform"
        else f"release: {repository.directory} {version}"
    )
    run(["git", "commit", "-m", message], repository.path)


def publish(repository: Repository, version: str, assets: list[Path]) -> None:
    tag = f"v{version}"
    progress(repository, 90, "push du commit sur main")
    run(["git", "push", "origin", "main"], repository.path)
    progress(repository, 93, f"création et push du tag {tag}")
    run(["git", "tag", "-a", tag, "-m", f"Release {tag}"], repository.path)
    run(["git", "push", "origin", tag], repository.path)
    progress(repository, 96, "création de la release GitHub")
    run(
        [
            "gh",
            "release",
            "create",
            tag,
            "--repo",
            repository.github,
            "--title",
            f"{repository.directory} {version}",
            "--generate-notes",
            *map(str, assets),
        ],
        repository.path,
    )
    verify_published_release(repository, version, assets)


def verify_published_release(
    repository: Repository,
    version: str,
    local_assets: list[Path],
) -> None:
    progress(repository, 98, "vérification distante des assets et références")
    tag = f"v{version}"
    with tempfile.TemporaryDirectory(
        prefix=f"ohana-{repository.key}-release-"
    ) as temporary:
        destination = Path(temporary)
        run(
            [
                "gh",
                "release",
                "download",
                tag,
                "--repo",
                repository.github,
                "--dir",
                str(destination),
            ],
            repository.path,
        )
        downloaded = {
            path.name: path for path in destination.iterdir() if path.is_file()
        }
        expected = {path.name: path for path in local_assets}
        if downloaded.keys() != expected.keys():
            missing = ", ".join(sorted(expected.keys() - downloaded.keys())) or "aucun"
            unexpected = (
                ", ".join(sorted(downloaded.keys() - expected.keys())) or "aucun"
            )
            raise ReleaseError(
                f"{repository.key}: release distante incomplète; "
                f"manquants={missing}; inattendus={unexpected}"
            )
        for name, local_path in expected.items():
            if sha256sum(local_path) != sha256sum(downloaded[name]):
                raise ReleaseError(
                    f"{repository.key}: hash distant différent pour {name}"
                )
    head = run(["git", "rev-parse", "HEAD"], repository.path, capture=True)
    origin = run(["git", "rev-parse", "origin/main"], repository.path, capture=True)
    tagged = run(["git", "rev-list", "-n", "1", tag], repository.path, capture=True)
    if len({head, origin, tagged}) != 1:
        raise ReleaseError(
            f"{repository.key}: HEAD, origin/main et {tag} ne pointent pas sur le même commit"
        )
    progress(repository, 100, "release publiée et vérifiée")


def selected(keys: list[str] | None) -> tuple[Repository, ...]:
    if not keys:
        return REPOSITORIES
    requested = set(keys)
    return tuple(
        repository for repository in REPOSITORIES if repository.key in requested
    )


def process_repository(repository: Repository) -> None:
    log = begin_log(repository)
    progress(repository, 0, f"démarrage — log : {log}")
    state = inspect_git_state(repository)
    if not state.has_local_changes:
        progress(repository, 100, "aucune différence locale avec GitHub")
        return
    progress(repository, 8, "modifications locales détectées")
    clear_progress_line()
    if state.status:
        changed_count = len(state.status.splitlines())
        print(
            f"[{repository.directory}] {changed_count} fichier(s) modifié(s) ou non suivi(s), "
            f"{state.ahead} commit(s) en avance."
        )
    else:
        print(
            f"[{repository.directory}] {state.ahead} commit(s) local(aux) en avance sur GitHub."
        )
    if not ask_yes_no(f"Créer une release pour {repository.directory} ?"):
        progress(repository, 100, "release ignorée à la demande de l’utilisateur")
        return
    current = local_version(repository)
    remote = github_version(repository)
    progress(repository, 12, "choix de la nouvelle version")
    new_version = request_new_version(repository, current, remote)
    if new_version == current:
        progress(repository, 18, "version locale déjà préparée, propagation inchangée")
    else:
        update_version_references(repository, current, new_version)
    normalize_version_file_line_endings(repository)
    try:
        run_checks(repository)
    except ReleaseError as error:
        raise ReleaseError(
            f"{repository.directory}: validation échouée; vérifiez le dépôt avant de reprendre. {error}"
        ) from error
    assets = prepare_assets(repository, new_version)
    commit_release(repository, new_version)
    publish(repository, new_version, assets)
    propagate_component_to_platform(
        repository,
        new_version,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo", action="append", choices=[r.key for r in REPOSITORIES]
    )
    args = parser.parse_args()
    try:
        for repository in selected(args.repo):
            process_repository(repository)
    except (
        EOFError,
        OSError,
        ReleaseError,
        subprocess.SubprocessError,
        json.JSONDecodeError,
        tomllib.TOMLDecodeError,
    ) as error:
        clear_progress_line()
        print(f"\nARRÊT : {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
