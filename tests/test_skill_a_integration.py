from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from hunter_agent.arxiv.client import ArxivClient
from hunter_agent.arxiv.parser import ArxivHtmlParser
from hunter_agent.db.repo import TalentRepository
from hunter_agent.skills.skill_a_daily_arxiv import run_skill_a


@unittest.skipUnless(
    os.getenv("RUN_INTEGRATION") == "1",
    "Set RUN_INTEGRATION=1 to run network integration tests.",
)
class TestSkillAIntegration(unittest.TestCase):
    def test_live_arxiv_fetch_and_persist(self) -> None:
        # Fixed past date for reproducibility.
        query_date = "2026-02-20"
        with TemporaryDirectory() as tmp_dir:
            repo = TalentRepository(Path(tmp_dir) / "hunter.db")
            repo.init_db()

            result = run_skill_a(
                payload={"date": query_date, "categories": ["cs.RO"]},
                arxiv_client=ArxivClient(timeout_seconds=30, max_results=200),
                html_parser=ArxivHtmlParser(timeout_seconds=30),
                repo=repo,
                persist_mentions=True,
            )
            self.assertEqual(result["date"], query_date)
            self.assertIn("records", result)
            self.assertIsInstance(result["records"], list)

            mentions = repo.export_table_rows("paper_author_mention")
            source_mentions = [m for m in mentions if m["source_date"] == query_date]
            self.assertEqual(len(source_mentions), len(result["records"]))

            if result["records"]:
                first = result["records"][0]
                self.assertIn("author_name", first)
                self.assertIn("paper_title", first)
                self.assertIn("arxiv_id", first)


if __name__ == "__main__":
    unittest.main()
