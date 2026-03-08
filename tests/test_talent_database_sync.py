from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from hunter_agent.db.repo import TalentRepository
from hunter_agent.skills.talent_database_sync import (
    run_talent_database_bulk_upsert,
    run_talent_database_sync,
)


class TestSkillB(unittest.TestCase):
    def test_find_and_upsert(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            repo = TalentRepository(Path(tmp_dir) / "hunter.db")
            repo.init_db()

            upsert_payload = {
                "action": "upsert",
                "profile": {
                    "name": "Zhang San",
                    "wechat": "zhangsan_robot",
                    "phone": "+86 13000000000",
                    "email": "zhangsan@example.com",
                    "project_categories": ["Manipulation算法", "其它:bionic hand"],
                    "education": "Master",
                    "institution": "Test University",
                    "grade_or_years": "2 years",
                },
            }
            upsert_result = run_talent_database_sync(upsert_payload, repo=repo)
            self.assertEqual(upsert_result["action"], "upsert")
            self.assertEqual(upsert_result["profile"]["talent"]["name"], "Zhang San")
            self.assertIn("dedup", upsert_result["profile"])

            find_payload = {"action": "find", "name": "Zhang San"}
            find_result = run_talent_database_sync(find_payload, repo=repo)
            self.assertEqual(find_result["action"], "find")
            self.assertEqual(len(find_result["matches"]), 1)
            self.assertEqual(
                find_result["matches"][0]["talent"]["institution"], "Test University"
            )

    def test_deduplicate_by_email(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            repo = TalentRepository(Path(tmp_dir) / "hunter.db")
            repo.init_db()

            run_talent_database_sync(
                {
                    "action": "upsert",
                    "profile": {
                        "name": "Alice Smith",
                        "email": "alice@example.com",
                    },
                },
                repo=repo,
            )
            run_talent_database_sync(
                {
                    "action": "upsert",
                    "profile": {
                        "name": "A. Smith",
                        "email": "alice@example.com",
                        "institution": "Example Lab",
                    },
                },
                repo=repo,
            )
            talent_rows = repo.export_table_rows("talent")
            self.assertEqual(len(talent_rows), 1)
            self.assertEqual(talent_rows[0]["name"], "A. Smith")
            self.assertEqual(talent_rows[0]["institution"], "Example Lab")

    def test_fuzzy_name_match_with_same_institution(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            repo = TalentRepository(Path(tmp_dir) / "hunter.db")
            repo.init_db()

            first = run_talent_database_sync(
                {
                    "action": "upsert",
                    "profile": {
                        "name": "Jonathan Lee",
                        "institution": "Embodied Lab",
                    },
                },
                repo=repo,
            )
            second = run_talent_database_sync(
                {
                    "action": "upsert",
                    "profile": {
                        "name": "Jonathon Lee",
                        "institution": "Embodied Lab",
                    },
                },
                repo=repo,
            )
            self.assertEqual(first["profile"]["talent"]["id"], second["profile"]["talent"]["id"])
            self.assertEqual(second["profile"]["operation"], "update")
            self.assertGreaterEqual(second["profile"]["dedup"]["score"], 50)

    def test_contact_conflict_forces_insert(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            repo = TalentRepository(Path(tmp_dir) / "hunter.db")
            repo.init_db()

            run_talent_database_sync(
                {
                    "action": "upsert",
                    "profile": {
                        "name": "Chris Wang",
                        "email": "chris.a@example.com",
                    },
                },
                repo=repo,
            )
            conflict = run_talent_database_sync(
                {
                    "action": "upsert",
                    "profile": {
                        "name": "Chris Wang",
                        "email": "chris.b@example.com",
                    },
                },
                repo=repo,
            )
            rows = repo.export_table_rows("talent")
            self.assertEqual(len(rows), 2)
            self.assertEqual(conflict["profile"]["operation"], "insert")
            self.assertTrue(conflict["profile"]["dedup"]["conflict"])
            self.assertTrue(conflict["profile"]["dedup"].get("forced_insert"))

    def test_bulk_upsert(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            repo = TalentRepository(Path(tmp_dir) / "hunter.db")
            repo.init_db()

            bulk_payload = {
                "profiles": [
                    {
                        "name": "Batch Alpha",
                        "email": "alpha@example.com",
                        "institution": "First Lab",
                    },
                    {
                        "name": "Batch Beta",
                        "email": "beta@example.com",
                        "institution": "Second Lab",
                    },
                ]
            }
            result = run_talent_database_bulk_upsert(bulk_payload, repo=repo)
            self.assertEqual(result["action"], "bulk-upsert")
            self.assertEqual(len(result["profiles"]), 2)
            self.assertTrue(all(item["operation"] == "insert" for item in result["profiles"]))
            names = {item["talent"]["name"] for item in result["profiles"]}
            self.assertEqual(names, {"Batch Alpha", "Batch Beta"})
            rows = repo.export_table_rows("talent")
            self.assertEqual(len(rows), 2)

    def test_export_from_skill(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            repo = TalentRepository(tmp_path / "hunter.db")
            repo.init_db()

            run_talent_database_sync(
                {
                    "action": "upsert",
                    "profile": {
                        "name": "Export Candidate",
                        "email": "export@example.com",
                    },
                },
                repo=repo,
            )
            export_path = tmp_path / "talents.csv"
            result = run_talent_database_sync(
                {"action": "export", "out_csv": str(export_path)},
                repo=repo,
            )
            self.assertEqual(result["action"], "export")
            self.assertEqual(result["output"], str(export_path))
            self.assertTrue(export_path.exists())
            self.assertGreater(export_path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
