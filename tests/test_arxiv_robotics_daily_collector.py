from __future__ import annotations

import unittest

from hunter_agent.arxiv.client import ArxivAuthor, ArxivPaper
from hunter_agent.skills.arxiv_robotics_daily_collector import (
    run_arxiv_robotics_daily_collector,
)


class _FakeArxivClient:
    def query_papers_by_date(self, query_date, categories):  # noqa: ANN001
        return [
            ArxivPaper(
                arxiv_id="2603.00001v1",
                title="Embodied Manipulation Benchmark",
                paper_url="https://arxiv.org/abs/2603.00001v1",
                html_url="https://arxiv.org/html/2603.00001v1",
                published_at="2026-03-01T00:00:00Z",
                categories=list(categories),
                authors=[
                    ArxivAuthor(name="Alice Smith"),
                    ArxivAuthor(name="Bob Lee"),
                ],
                summary="This paper explores embodied manipulation.",
            )
        ]


class _FakeArxivHtmlParser:
    def enrich_affiliation_info(self, paper: ArxivPaper) -> ArxivPaper:
        paper.affiliation_info = (
            "UniForce\nZhuo Chen1, Fei Ni2, Kaiyao Luo1\n"
            "1 University A 2 University B"
        )
        return paper


class TestArxivRoboticsDailyCollector(unittest.TestCase):
    def test_collect_daily_paper_records(self) -> None:
        result = run_arxiv_robotics_daily_collector(
            payload={"date": "2026-03-01", "categories": ["cs.RO"]},
            arxiv_client=_FakeArxivClient(),
            html_parser=_FakeArxivHtmlParser(),
            repo=None,
            persist_mentions=False,
        )
        self.assertEqual(result["date"], "2026-03-01")
        self.assertEqual(len(result["records"]), 1)
        first = result["records"][0]
        self.assertEqual(first["paper_title"], "Embodied Manipulation Benchmark")
        self.assertEqual(first["paper_url"], "https://arxiv.org/abs/2603.00001v1")
        self.assertEqual(first["authors"], ["Alice Smith", "Bob Lee"])
        self.assertIn("University A", first["affiliation_info"])
        self.assertEqual(first["paper_summary"], "This paper explores embodied manipulation.")


if __name__ == "__main__":
    unittest.main()
