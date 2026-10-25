from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
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


class UnattendedReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(dir=release_all.ROOT)
        self.directory = Path(self.temporary.name).name
        self.repository = release_all.Repository(
            "agent", self.directory, "owner/repo", "python"
        )
        release_all.OPTIONS = release_all.Options()

    def tearDown(self) -> None:
        release_all.OPTIONS = release_all.Options()
        release_all.PROGRESS_WIDTH = 0
        self.temporary.cleanup()

    def _git(self, *arguments: str) -> None:
        subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *arguments],
            cwd=self.repository.path,
            check=True,
            capture_output=True,
        )

    def test_yes_answers_every_confirmation_without_reading_input(self) -> None:
        release_all.OPTIONS.yes = True
        with patch("builtins.input", side_effect=AssertionError("no prompt")):
            with redirect_stdout(StringIO()):
                self.assertTrue(release_all.ask_yes_no("Créer une release ?"))

    def test_version_options_name_a_repository_and_a_version(self) -> None:
        self.assertEqual(
            release_all.parse_version_options(["agent=1.50.0", "vision=1.40.0"]),
            {"agent": "1.50.0", "vision": "1.40.0"},
        )
        for bad in ("1.50.0", "nowhere=1.0.0", "agent=1.5"):
            with self.subTest(bad=bad), self.assertRaises(release_all.ReleaseError):
                release_all.parse_version_options([bad])

    def test_a_requested_version_is_used_without_a_prompt(self) -> None:
        release_all.OPTIONS.versions = {"agent": "1.50.0"}
        with (
            patch("builtins.input", side_effect=AssertionError("no prompt")),
            patch.object(release_all, "execute") as execute,
            redirect_stdout(StringIO()),
        ):
            execute.side_effect = [
                SimpleCompleted(1),  # local tag absent
                SimpleCompleted(2),  # remote tag absent
            ]
            version = release_all.request_new_version(
                self.repository, "1.49.0", "1.49.0"
            )
        self.assertEqual(version, "1.50.0")

    def test_the_release_stages_only_what_it_changed(self) -> None:
        path = self.repository.path
        self._git("init", "-q", "-b", "main")
        (path / "version.txt").write_text("1.0.0\n", encoding="utf-8")
        (path / "pending.txt").write_text("work\n", encoding="utf-8")
        (path / "other.txt").write_text("keep\n", encoding="utf-8")
        self._git("add", ".")
        self._git("commit", "-q", "-m", "init")
        (path / "pending.txt").write_text("work in progress\n", encoding="utf-8")
        baseline = release_all.tracked_changes(self.repository)

        (path / "version.txt").write_text("1.1.0\n", encoding="utf-8")
        (path / "untracked.txt").write_text("graphify\n", encoding="utf-8")

        self.assertEqual(
            release_all.files_edited_since(self.repository, baseline), ["version.txt"]
        )
        # A file already dirty that the release edits again is staged too.
        (path / "pending.txt").write_text("work in progress, bumped\n", encoding="utf-8")
        self.assertEqual(
            release_all.files_edited_since(self.repository, baseline),
            ["pending.txt", "version.txt"],
        )

    def test_commit_release_never_adds_everything(self) -> None:
        with (
            patch.object(release_all, "progress"),
            patch.object(release_all, "run") as run,
            patch.object(release_all, "execute") as execute,
        ):
            execute.return_value.returncode = 1
            release_all.commit_release(self.repository, "9.9.9", ["pyproject.toml"])
            release_all.commit_release(self.repository, "9.9.9")
        commands = [call.args[0] for call in run.call_args_list]
        self.assertIn(["git", "add", "--", "pyproject.toml"], commands)
        self.assertIn(["git", "add", "--update"], commands)
        self.assertNotIn(["git", "add", "--all"], commands)

    def test_a_second_release_the_same_day_is_refused_unless_urgent(self) -> None:
        with patch.object(release_all, "todays_release", return_value=True):
            with self.assertRaisesRegex(release_all.ReleaseError, "une release"):
                release_all.ensure_one_release_a_day(self.repository)
            release_all.OPTIONS.urgent = True
            release_all.ensure_one_release_a_day(self.repository)
        release_all.OPTIONS.urgent = False
        with patch.object(release_all, "todays_release", return_value=False):
            release_all.ensure_one_release_a_day(self.repository)

    def test_todays_release_compares_the_publication_date(self) -> None:
        now = datetime.now().astimezone()
        for published, expected in (
            (now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"), True),
            ((now - timedelta(days=2)).astimezone(timezone.utc).isoformat().replace("+00:00", "Z"), False),
        ):
            with self.subTest(published=published):
                with patch.object(release_all, "execute") as execute:
                    execute.return_value = SimpleCompleted(0, published + "\n")
                    self.assertEqual(release_all.todays_release(self.repository), expected)
        with patch.object(release_all, "execute") as execute:
            execute.return_value = SimpleCompleted(1, "")
            self.assertFalse(release_all.todays_release(self.repository))


class ChangelogPromotionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(dir=release_all.ROOT)
        self.repository = release_all.Repository(
            "agent", Path(self.temporary.name).name, "owner/repo", "python"
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _changelog(self, text: str) -> Path:
        path = self.repository.path / "CHANGELOG.md"
        path.write_text(text, encoding="utf-8", newline="")
        return path

    def test_unreleased_notes_become_the_release_section_and_the_notes(self) -> None:
        path = self._changelog(
            "# CHANGELOG\n\n## Non publié\n\n- Première entrée. Détail.\n- Seconde.\n\n"
            "## [1.0.0] — 2026-01-01 — Début\n\n- Ancien.\n"
        )

        notes = release_all.promote_changelog(
            self.repository, "1.1.0", today="2026-10-26"
        )

        self.assertEqual(notes, "- Première entrée. Détail.\n- Seconde.\n")
        text = path.read_text(encoding="utf-8")
        self.assertIn(
            "## Non publié\n\n## [1.1.0] — 2026-10-26 — Première entrée\n\n"
            "- Première entrée. Détail.\n- Seconde.\n\n## [1.0.0]",
            text,
        )
        self.assertEqual(text.count("## Non publié"), 1)

    def test_an_empty_unreleased_section_leaves_the_file_alone(self) -> None:
        original = "# CHANGELOG\n\n## Non publié\n\n## [1.0.0] — 2026-01-01 — Début\n\n- Ancien.\n"
        path = self._changelog(original)

        self.assertIsNone(release_all.promote_changelog(self.repository, "1.1.0"))
        self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_a_repository_without_changelog_is_not_an_error(self) -> None:
        self.assertIsNone(release_all.promote_changelog(self.repository, "1.1.0"))

    def test_windows_line_endings_are_kept(self) -> None:
        path = self._changelog("# C\r\n\r\n## Non publié\r\n\r\n- Entrée.\r\n")

        release_all.promote_changelog(self.repository, "2.0.0", today="2026-10-26")

        raw = path.read_bytes()
        self.assertIn(b"\r\n", raw)
        self.assertNotIn(b"\n\n", raw.replace(b"\r\n", b""))


class SimpleCompleted:
    def __init__(self, returncode: int, stdout: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = ""


if __name__ == "__main__":
    unittest.main()
