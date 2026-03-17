from __future__ import annotations

from pathlib import Path
import sqlite3
import unittest

from hunter_agent.common.enums import LEGACY_PROJECT_CATEGORY_ALIASES
from hunter_agent.db.repo import TalentRepository
from hunter_agent.skills.talent_database_sync import (
    run_talent_database_bulk_upsert,
    run_talent_database_sync,
)
from tests.support import workspace_temp_dir


def _legacy_alias_for(slug: str, exclude: set[str] | None = None) -> str:
    excluded = exclude or set()
    for key, value in LEGACY_PROJECT_CATEGORY_ALIASES.items():
        if value == slug and key not in excluded:
            return key
    raise AssertionError(f"Missing legacy alias for {slug}")


class TestSkillB(unittest.TestCase):
    def test_find_and_upsert(self) -> None:
        with workspace_temp_dir() as tmp_path:
            repo = TalentRepository(tmp_path / "hunter.db")
            repo.init_db()

            upsert_payload = {
                "action": "upsert",
                "profile": {
                    "name": "Zhang San",
                    "wechat": "zhangsan_robot",
                    "phone": "+86 13000000000",
                    "email": "zhangsan@example.com",
                    "project_categories": ["manipulation", "other:bionic hand"],
                    "education": "Master",
                    "institution": "Test University",
                    "position": "masters",
                    "grade_or_years": "2 years",
                    "city": "Shanghai",
                    "country": "China",
                    "graduation_time": "2024",
                    "research_fields": "robot learning, manipulation",
                    "homepage_url": "https://example.com/zhangsan",
                    "source_links": "https://example.com/profile",
                    "evidence_summary": "Matched lab profile.",
                },
            }
            upsert_result = run_talent_database_sync(upsert_payload, repo=repo)
            self.assertEqual(upsert_result["action"], "upsert")
            self.assertEqual(upsert_result["profile"]["talent"]["name"], "Zhang San")
            self.assertIn("dedup", upsert_result["profile"])
            self.assertEqual(upsert_result["profile"]["talent"]["city"], "Shanghai")
            self.assertEqual(upsert_result["profile"]["talent"]["country"], "China")
            self.assertEqual(upsert_result["profile"]["talent"]["position"], "masters")
            self.assertEqual(
                upsert_result["profile"]["talent"]["research_fields"],
                "robot learning, manipulation",
            )

            find_payload = {"action": "find", "name": "Zhang San"}
            find_result = run_talent_database_sync(find_payload, repo=repo)
            self.assertEqual(find_result["action"], "find")
            self.assertEqual(len(find_result["matches"]), 1)
            self.assertEqual(
                find_result["matches"][0]["talent"]["institution"], "Test University"
            )
            self.assertEqual(find_result["matches"][0]["talent"]["homepage_url"], "https://example.com/zhangsan")

    def test_position_must_use_supported_values(self) -> None:
        with workspace_temp_dir() as tmp_path:
            repo = TalentRepository(tmp_path / "hunter.db")
            repo.init_db()

            with self.assertRaisesRegex(ValueError, "position must be one of"):
                run_talent_database_sync(
                    {
                        "action": "upsert",
                        "profile": {
                            "name": "Invalid Position",
                            "position": "教授助理",
                        },
                    },
                    repo=repo,
                )

    def test_deduplicate_by_email(self) -> None:
        with workspace_temp_dir() as tmp_path:
            repo = TalentRepository(tmp_path / "hunter.db")
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
        with workspace_temp_dir() as tmp_path:
            repo = TalentRepository(tmp_path / "hunter.db")
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
        with workspace_temp_dir() as tmp_path:
            repo = TalentRepository(tmp_path / "hunter.db")
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
        with workspace_temp_dir() as tmp_path:
            repo = TalentRepository(tmp_path / "hunter.db")
            repo.init_db()

            bulk_payload = {
                "profiles": [
                    {
                        "name": "Batch Alpha",
                        "email": "alpha@example.com",
                        "institution": "First Lab",
                        "project_categories": ["embedded-systems"],
                    },
                    {
                        "name": "Batch Beta",
                        "email": "beta@example.com",
                        "institution": "Second Lab",
                        "project_categories": ["other:custom hardware"],
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

    def test_update_keeps_existing_optional_fields_when_new_values_are_empty(self) -> None:
        with workspace_temp_dir() as tmp_path:
            repo = TalentRepository(tmp_path / "hunter.db")
            repo.init_db()

            run_talent_database_sync(
                {
                    "action": "upsert",
                    "profile": {
                        "name": "Optional Fields",
                        "email": "optional@example.com",
                        "city": "Hong Kong",
                        "country": "China",
                        "research_fields": "robotics",
                    },
                },
                repo=repo,
            )
            result = run_talent_database_sync(
                {
                    "action": "upsert",
                    "profile": {
                        "name": "Optional Fields",
                        "email": "optional@example.com",
                    },
                },
                repo=repo,
            )

            self.assertEqual(result["profile"]["talent"]["city"], "Hong Kong")
            self.assertEqual(result["profile"]["talent"]["country"], "China")
            self.assertEqual(result["profile"]["talent"]["research_fields"], "robotics")

    def test_export_from_skill(self) -> None:
        with workspace_temp_dir() as tmp_path:
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

    def test_legacy_category_aliases_are_normalized_on_input(self) -> None:
        with workspace_temp_dir() as tmp_path:
            repo = TalentRepository(tmp_path / "hunter.db")
            repo.init_db()

            legacy_manipulation = _legacy_alias_for("manipulation", exclude={"manipulation"})
            result = run_talent_database_sync(
                {
                    "action": "upsert",
                    "profile": {
                        "name": "Legacy Category",
                        "project_categories": [
                            legacy_manipulation,
                            "\u5176\u4ed6:legacy detail",
                        ],
                    },
                },
                repo=repo,
            )

            tags = result["profile"]["project_tags"]
            self.assertEqual(tags[0]["category"], "manipulation")
            self.assertEqual(tags[1]["category"], "other")
            self.assertEqual(tags[1]["other_text"], "legacy detail")

    def test_legacy_project_tags_are_normalized_on_init(self) -> None:
        with workspace_temp_dir() as tmp_path:
            repo = TalentRepository(tmp_path / "hunter.db")
            repo.init_db()
            legacy_manipulation = _legacy_alias_for("manipulation", exclude={"manipulation"})
            legacy_other = _legacy_alias_for("other", exclude={"other"})

            conn = sqlite3.connect(repo.db_path)
            try:
                conn.execute(
                    """
                    INSERT INTO talent (name, normalized_name, created_at, updated_at)
                    VALUES ('Legacy DB', 'legacydb', datetime('now'), datetime('now'))
                    """
                )
                talent_id = conn.execute(
                    "SELECT id FROM talent WHERE normalized_name = 'legacydb'"
                ).fetchone()[0]
                conn.execute(
                    """
                    INSERT INTO talent_project_tag (talent_id, category, other_text)
                    VALUES (?, ?, ?), (?, ?, ?)
                    """,
                    (
                        talent_id,
                        legacy_manipulation,
                        None,
                        talent_id,
                        legacy_other,
                        "legacy detail",
                    ),
                )
                conn.commit()
            finally:
                conn.close()

            repo.init_db()
            tags = repo.export_table_rows("talent_project_tag")
            categories = {(tag["category"], tag["other_text"]) for tag in tags}
            self.assertIn(("manipulation", None), categories)
            self.assertIn(("other", "legacy detail"), categories)


if __name__ == "__main__":
    unittest.main()
