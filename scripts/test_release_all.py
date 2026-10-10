from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import release_all


class VersionPropagationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(dir=release_all.ROOT)
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        release_all.PROGRESS_WIDTH = 0
        self.temporary.cleanup()

    def test_release_commit_titles_follow_component_and_platform_conventions(self):
        for key, expected in (
            ("agent", "release: Ohana-Agent 9.9.9"),
            ("platform", "release: compose Platform 9.9.9"),
        ):
            with self.subTest(key=key):
                repository = next(r for r in release_all.REPOSITORIES if r.key == key)
                with (
                    patch.object(release_all, "progress"),
                    patch.object(release_all, "run") as run,
                    patch.object(release_all, "execute") as execute,
                ):
                    execute.return_value.returncode = 1
                    release_all.commit_release(repository, "9.9.9")
                run.assert_any_call(["git", "commit", "-m", expected], repository.path)

    def test_progress_reuses_one_line_until_completion(self) -> None:
        repository = next(
            item for item in release_all.REPOSITORIES if item.key == "agent"
        )
        output = StringIO()

        with redirect_stdout(output):
            release_all.progress(repository, 0, "démarrage")
            release_all.progress(repository, 2, "synchronisation")
            release_all.progress(
                repository,
                100,
                "aucune différence locale avec GitHub",
            )

        rendered = output.getvalue()

        self.assertEqual(rendered.count("\n"), 1)
        self.assertIn(
            "\r[Ohana-Agent] 100% - aucune différence locale avec GitHub",
            rendered,
        )

    def copy_repository(
        self,
        key: str,
        paths: tuple[str, ...],
    ) -> release_all.Repository:
        source = next(
            repository
            for repository in release_all.REPOSITORIES
            if repository.key == key
        )

        destination = self.root / source.directory

        for relative in paths:
            source_path = source.path / relative
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target)

        return release_all.Repository(
            key,
            str(destination),
            source.github,
            source.kind,
        )

    def test_agent_authoritative_version_and_metadata_test_are_updated(
        self,
    ) -> None:
        repository = self.copy_repository(
            "agent",
            (
                "pyproject.toml",
                "tests/test_package_metadata.py",
            ),
        )

        old = release_all.local_version(repository)
        new = release_all.next_patch(old)

        release_all.update_version_references(
            repository,
            old,
            new,
        )

        self.assertEqual(
            release_all.local_version(repository),
            new,
        )

        package_metadata_test = (
            repository.path / "tests/test_package_metadata.py"
        ).read_text(encoding="utf-8")

        self.assertIn(
            f'assert project["version"] == "{new}"',
            package_metadata_test,
        )

        self.assertNotIn(
            f'assert project["version"] == "{old}"',
            package_metadata_test,
        )

    def test_vision_authoritative_version_is_updated(self) -> None:
        repository = self.copy_repository(
            "vision",
            ("pyproject.toml",),
        )

        old = release_all.local_version(repository)
        new = release_all.next_patch(old)

        release_all.update_version_references(
            repository,
            old,
            new,
        )

        self.assertEqual(
            release_all.local_version(repository),
            new,
        )

    def test_version_files_are_normalized_to_lf(self) -> None:
        repository = self.copy_repository(
            "vision",
            ("pyproject.toml",),
        )

        path = repository.path / "pyproject.toml"
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))

        release_all.normalize_version_file_line_endings(repository)

        self.assertNotIn(
            b"\r",
            path.read_bytes(),
        )

    def test_installer_versions_update_without_rewriting_dynamic_update_tests(
        self,
    ) -> None:
        repository = self.copy_repository(
            "installer",
            (
                "pyproject.toml",
                "src/ohana_installer/version.py",
                "tests/test_interactive.py",
                "tests/test_update.py",
            ),
        )

        old = release_all.local_version(repository)
        new = release_all.next_patch(old)
        update_path = repository.path / "tests/test_update.py"
        update_before = update_path.read_bytes()

        release_all.update_version_references(
            repository,
            old,
            new,
        )

        self.assertEqual(
            release_all.local_version(repository),
            new,
        )

        self.assertEqual(update_path.read_bytes(), update_before)
        self.assertIn(
            f'__version__ = "{new}"',
            (repository.path / "src/ohana_installer/version.py").read_text(
                encoding="utf-8"
            ),
        )

    def test_katsuyu_runtime_and_tests_are_updated(self) -> None:
        repository = self.copy_repository(
            "katsuyu",
            (
                "pyproject.toml",
                "ohana_katsuyu/__init__.py",
                "tests/test_package.py",
                "tests/test_setup.py",
                "tests/test_updates.py",
            ),
        )

        old = release_all.local_version(repository)
        new = release_all.next_patch(old)

        release_all.update_version_references(
            repository,
            old,
            new,
        )

        self.assertEqual(
            release_all.local_version(repository),
            new,
        )

        self.assertIn(
            f"Ohana-Katsuyu/{new}",
            (repository.path / "tests/test_updates.py").read_text(encoding="utf-8"),
        )

    def test_shizune_version_json_is_updated(self) -> None:
        repository = self.copy_repository(
            "shizune",
            ("Shizune/PWA/version.json",),
        )

        old = release_all.local_version(repository)
        new = release_all.next_patch(old)

        release_all.update_version_references(
            repository,
            old,
            new,
        )

        self.assertEqual(
            release_all.local_version(repository),
            new,
        )

    def test_platform_adds_a_release_without_overwriting_history(
        self,
    ) -> None:
        repository = self.copy_repository(
            "platform",
            (
                "release-manifest.yaml",
                "release-catalog.yaml",
            ),
        )

        old = release_all.local_version(repository)
        new = release_all.next_patch(old)

        release_all.update_platform_version(
            repository,
            old,
            new,
        )

        self.assertEqual(
            release_all.local_version(repository),
            new,
        )

        catalog = (repository.path / "release-catalog.yaml").read_text(encoding="utf-8")

        self.assertIn(
            f'platform_version: "{new}"',
            catalog,
        )

        self.assertIn(
            f'platform_version: "{old}"',
            catalog,
        )

        self.assertEqual(
            catalog.count("status: recommended"),
            1,
        )

    def test_component_release_updates_next_platform_composition(
        self,
    ) -> None:
        platform = self.copy_repository(
            "platform",
            (
                "release-manifest.yaml",
                "release-catalog.yaml",
            ),
        )

        vision = next(item for item in release_all.REPOSITORIES if item.key == "vision")

        manifest_path = platform.path / "release-manifest.yaml"

        component_old = release_all.manifest_component_versions(
            manifest_path.read_text(encoding="utf-8")
        )["vision"]

        component_new = release_all.next_patch(component_old)

        release_all.propagate_component_to_platform(
            vision,
            component_new,
            platform.path,
        )

        platform_old = release_all.local_version(platform)
        platform_new = release_all.next_patch(platform_old)

        release_all.update_platform_version(
            platform,
            platform_old,
            platform_new,
        )

        catalog = (platform.path / "release-catalog.yaml").read_text(encoding="utf-8")

        first, second = catalog.split(
            "  - platform_version:",
            2,
        )[1:]

        self.assertIn(
            f'vision_version: "{component_new}"',
            first,
        )

        self.assertIn(
            f'vision_version: "{component_old}"',
            second,
        )

    def test_platform_sync_updates_installer_mirrors_and_expectations(
        self,
    ) -> None:
        platform = self.copy_repository(
            "platform",
            (
                "release-manifest.yaml",
                "release-catalog.yaml",
            ),
        )

        installer = self.copy_repository(
            "installer",
            (
                "config/release-manifest.yaml",
                "config/release-catalog.yaml",
                "tests/test_manifest.py",
                "tests/test_release_catalog.py",
            ),
        )

        old = release_all.local_version(platform)
        new = release_all.next_patch(old)

        release_all.update_platform_version(
            platform,
            old,
            new,
        )

        release_all.sync_platform_to_installer(
            platform,
            installer.path,
        )

        mirrored = (installer.path / "config/release-manifest.yaml").read_text(
            encoding="utf-8"
        )

        manifest_test = (installer.path / "tests/test_manifest.py").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            f'version: "{new}"',
            mirrored,
        )

        self.assertIn(
            f'assert manifest.platform_version == "{new}"',
            manifest_test,
        )

    def test_prepared_local_version_can_be_kept(self) -> None:
        repository = next(
            item for item in release_all.REPOSITORIES if item.key == "installer"
        )

        results = (
            subprocess.CompletedProcess([], 1, "", ""),
            subprocess.CompletedProcess([], 2, "", ""),
        )

        with (
            patch(
                "builtins.input",
                return_value="1.14.2",
            ),
            patch.object(
                release_all,
                "execute",
                side_effect=results,
            ),
        ):
            selected = release_all.request_new_version(
                repository,
                "1.14.2",
                "1.14.1",
            )

        self.assertEqual(
            selected,
            "1.14.2",
        )

    def test_current_github_version_cannot_be_reused(self) -> None:
        repository = next(
            item for item in release_all.REPOSITORIES if item.key == "installer"
        )

        with (
            patch(
                "builtins.input",
                return_value="1.14.2",
            ),
            self.assertRaises(release_all.ReleaseError),
        ):
            release_all.request_new_version(
                repository,
                "1.14.2",
                "1.14.2",
            )

    def test_component_release_can_skip_platform_recorded_version(self) -> None:
        platform = self.copy_repository(
            "platform",
            (
                "release-manifest.yaml",
                "release-catalog.yaml",
            ),
        )

        agent = next(item for item in release_all.REPOSITORIES if item.key == "agent")

        manifest_path = platform.path / "release-manifest.yaml"

        component_old = release_all.manifest_component_versions(
            manifest_path.read_text(encoding="utf-8")
        )["agent"]

        intermediate = release_all.next_patch(component_old)
        component_new = release_all.next_patch(intermediate)

        release_all.propagate_component_to_platform(
            agent,
            component_new,
            platform.path,
        )

        manifest = manifest_path.read_text(encoding="utf-8")

        self.assertIn(
            f'    version: "{component_new}"',
            manifest,
        )
        self.assertIn(
            f"    release_tag: v{component_new}",
            manifest,
        )
        self.assertIn(
            f"ohana_agent-{component_new}",
            manifest,
        )


if __name__ == "__main__":
    unittest.main()
