from __future__ import annotations

from datetime import date
import unittest

from hunter_agent.arxiv.client import ArxivAuthor, ArxivPaper
from hunter_agent.skills.arxiv_range_authors import run_arxiv_range_authors


class _FakeArxivClient:
    def query_papers_by_date(self, query_date, categories):  # noqa: ANN001
        suffix = query_date.strftime("%Y%m%d")
        return [
            ArxivPaper(
                arxiv_id=f"{suffix}.00001v1",
                title=f"Paper {suffix}",
                paper_url=f"https://arxiv.org/abs/{suffix}.00001v1",
                html_url=f"https://arxiv.org/html/{suffix}.00001v1",
                published_at=f"{query_date.isoformat()}T00:00:00Z",
                categories=list(categories),
                authors=[
                    ArxivAuthor(name="Chen Li"),
                    ArxivAuthor(name="Alice Smith"),
                ],
                summary=f"Summary {suffix}",
            )
        ]


class _FakeArxivHtmlParser:
    def enrich_affiliation_info(self, paper: ArxivPaper) -> ArxivPaper:
        paper.affiliation_info = "Embodied AI Lab"
        return paper


class TestArxivRangeAuthors(unittest.TestCase):
    def test_collect_range_authors(self) -> None:
        result = run_arxiv_range_authors(
            payload={
                "start_date": "2026-03-02",
                "end_date": "2026-03-03",
                "categories": ["cs.RO"],
            },
            arxiv_client=_FakeArxivClient(),
            html_parser=_FakeArxivHtmlParser(),
        )

        self.assertEqual(result["start_date"], "2026-03-02")
        self.assertEqual(result["end_date"], "2026-03-03")
        self.assertEqual(len(result["authors"]), 2)
        self.assertEqual(result["authors"][0]["author_name"], "Alice Smith")
        self.assertEqual(result["authors"][0]["paper_count"], 2)

    def test_defaults_to_previous_calendar_week(self) -> None:
        result = run_arxiv_range_authors(
            payload={"categories": ["cs.RO"]},
            arxiv_client=_FakeArxivClient(),
            html_parser=_FakeArxivHtmlParser(),
            today=date(2026, 3, 13),
        )

        self.assertEqual(result["start_date"], "2026-03-02")
        self.assertEqual(result["end_date"], "2026-03-08")


if __name__ == "__main__":
    unittest.main()
