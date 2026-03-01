from __future__ import annotations

import unittest

from hunter_agent.arxiv.client import ArxivAuthor, ArxivPaper
from hunter_agent.skills.skill_a_daily_arxiv import run_skill_a


class _FakeArxivClient:
    def query_papers_by_date(self, query_date, categories):  # noqa: ANN001
        return [
            ArxivPaper(
                arxiv_id="2603.00001",
                title="Embodied Manipulation Benchmark",
                paper_url="https://arxiv.org/abs/2603.00001",
                published_at="2026-03-01T00:00:00Z",
                categories=list(categories),
                authors=[
                    ArxivAuthor(name="Alice Smith", affiliation="Example University"),
                    ArxivAuthor(name="Bob Lee", affiliation=None),
                ],
            )
        ]


class _FakeArxivHtmlParser:
    def enrich_missing_affiliations(self, paper: ArxivPaper) -> ArxivPaper:
        for author in paper.authors:
            if author.name == "Bob Lee" and not author.affiliation:
                author.affiliation = "Example Robotics Lab"
        return paper


class TestSkillA(unittest.TestCase):
    def test_collect_daily_author_records(self) -> None:
        result = run_skill_a(
            payload={"date": "2026-03-01", "categories": ["cs.RO"]},
            arxiv_client=_FakeArxivClient(),
            html_parser=_FakeArxivHtmlParser(),
            repo=None,
            persist_mentions=False,
        )
        self.assertEqual(result["date"], "2026-03-01")
        self.assertEqual(len(result["records"]), 2)
        bob = [row for row in result["records"] if row["author_name"] == "Bob Lee"][0]
        self.assertEqual(bob["affiliation"], "Example Robotics Lab")


if __name__ == "__main__":
    unittest.main()
