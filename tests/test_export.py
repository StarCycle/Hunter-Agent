from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from hunter_agent.common.schemas import TalentProfile
from hunter_agent.db.repo import TalentRepository
from hunter_agent.services.export_service import ExportService


class TestExportService(unittest.TestCase):
    def test_export_csv(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            repo = TalentRepository(tmp_path / "hunter.db")
            repo.init_db()
            repo.upsert_talent(
                TalentProfile(
                    name="李四",
                    email="lisi@example.com",
                    project_categories=["机器人底层控制和软件"],
                    institution="测试研究院",
                )
            )
            exporter = ExportService(repo=repo)

            csv_path = exporter.export_flat_csv(tmp_path / "talents.csv")

            self.assertTrue(csv_path.exists())
            self.assertGreater(csv_path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
