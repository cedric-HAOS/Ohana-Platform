"""The post-deployment recette tells what it proved and what is still pending."""

from __future__ import annotations

import unittest

import recette

RULES = [{"id": rule, "state": "ok", "nodes": []} for rule in recette.EXPECTED_RULES]


def routes(**overrides):
    base = {
        "/api/runtime/vitals": {"version": "1.40.0"},
        "/api/administration/agent/vitals": {
            "versions": {"agent": {"installed": "1.50.0"}}
        },
        "/api/administration/tsunade/preventive": {"checks": RULES, "watch": []},
        "/api/administration/tsunade/backups/restore-tests": {
            "icloud": {"connected": True, "state": "connected", "checked_at": "t"},
            "targets": [
                {"target": "infra-01", "state": "never_tested", "integrity": {"outcome": "ok"}}
            ],
        },
    }
    base.update(overrides)
    return lambda path: base[path]


def shell(path_count="0"):
    def run(command: str) -> str:
        if "grep -c httpx" in command:
            return path_count
        if "wc -l" in command and "journalctl" in command:
            return "120"
        if "grep -vc" in command:
            return "0"
        return "absent"

    return run


def statuses(result: recette.Recette) -> dict[str, str]:
    return {label: status for label, status, _ in result.results}


class RecetteTests(unittest.TestCase):
    def test_a_healthy_deployment_passes(self) -> None:
        result = recette.run("1.50.0", "1.40.0", fetch=routes(), shell=shell())

        self.assertTrue(result.passed())
        self.assertNotIn("KO", statuses(result).values())

    def test_an_old_version_or_missing_rules_fail(self) -> None:
        old = routes(
            **{
                "/api/runtime/vitals": {"version": "1.38.1"},
                "/api/administration/tsunade/preventive": {
                    "checks": RULES[:2],
                    "watch": [],
                },
            }
        )

        result = recette.run("1.50.0", "1.40.0", fetch=old, shell=shell())

        self.assertFalse(result.passed())
        found = statuses(result)
        self.assertEqual(found["Version de Vision"], "KO")
        self.assertEqual(found["Règles préventives livrées"], "KO")

    def test_httpx_lines_in_the_journal_fail(self) -> None:
        result = recette.run("1.50.0", "1.40.0", fetch=routes(), shell=shell("14"))

        self.assertEqual(statuses(result)["Journal de l'Agent sans lignes httpx"], "KO")

    def test_first_readings_are_pending_not_failures(self) -> None:
        pending = routes(
            **{
                "/api/administration/tsunade/backups/restore-tests": {
                    "icloud": None,
                    "targets": [],
                }
            }
        )

        result = recette.run("1.50.0", "1.40.0", fetch=pending, shell=shell())

        self.assertTrue(result.passed())
        found = statuses(result)
        self.assertEqual(found["État de la session iCloud"], "EN ATTENTE")
        self.assertEqual(found["Registre des restaurations"], "EN ATTENTE")

    def test_a_broken_archive_or_iCloud_session_fails(self) -> None:
        broken = routes(
            **{
                "/api/administration/tsunade/backups/restore-tests": {
                    "icloud": {"connected": False, "state": "session_expired", "checked_at": "t"},
                    "targets": [
                        {"target": "ha-01", "state": "verified", "integrity": {"outcome": "hash_mismatch"}}
                    ],
                }
            }
        )

        result = recette.run("1.50.0", "1.40.0", fetch=broken, shell=shell())

        found = statuses(result)
        self.assertEqual(found["État de la session iCloud"], "KO")
        self.assertEqual(found["Intégrité des archives relues"], "KO")

    def test_an_unreachable_vision_is_reported_not_raised(self) -> None:
        def down(path: str):
            raise OSError("connexion refusée")

        result = recette.run("1.50.0", "1.40.0", fetch=down, shell=shell())

        self.assertFalse(result.passed())

    def test_urgent_items_are_flagged_without_failing(self) -> None:
        urgent = routes(
            **{
                "/api/administration/tsunade/preventive": {
                    "checks": RULES,
                    "watch": [{"title": "HA-01 : archive altérée", "urgent": True}],
                }
            }
        )

        result = recette.run("1.50.0", "1.40.0", fetch=urgent, shell=shell())

        self.assertEqual(
            statuses(result)["Éléments urgents de la maintenance préventive"],
            "ATTENTION",
        )
        self.assertTrue(result.passed())


if __name__ == "__main__":
    unittest.main()
