from __future__ import annotations

from pathlib import Path
import unittest
import csv

from hunter_agent.common.schemas import TalentProfile
from hunter_agent.db.repo import TalentRepository
from hunter_agent.services.export_service import ExportService
from tests.support import workspace_temp_dir


class TestExportService(unittest.TestCase):
    def test_export_csv(self) -> None:
        with workspace_temp_dir() as tmp_path:
            repo = TalentRepository(tmp_path / "hunter.db")
            repo.init_db()
            repo.upsert_talent(
                TalentProfile(
                    name="Li Si",
                    email="lisi@example.com",
                    project_categories=["robot-control-software"],
                    institution="Test Institute",
                    position="phd",
                    city="Shenzhen",
                    country="China",
                    graduation_time="2025",
                    research_fields="robot control",
                )
            )
            exporter = ExportService(repo=repo)

            csv_path = exporter.export_flat_csv(tmp_path / "talents.csv")

            self.assertTrue(csv_path.exists())
            self.assertGreater(csv_path.stat().st_size, 0)
            with csv_path.open("r", encoding="utf-8-sig", newline="") as fp:
                reader = csv.DictReader(fp)
                rows = list(reader)
            self.assertNotIn("talent_id", rows[0])
            self.assertEqual(rows[0]["position"], "phd")
            self.assertEqual(rows[0]["city"], "Shenzhen")
            self.assertEqual(rows[0]["country"], "China")
            self.assertEqual(rows[0]["graduation_time"], "2025")
            self.assertEqual(rows[0]["research_fields"], "robot control")


if __name__ == "__main__":
    unittest.main()
