from __future__ import annotations

from datetime import date

from hunter_agent.arxiv.client import ArxivClient
from hunter_agent.arxiv.parser import ArxivHtmlParser
from hunter_agent.common.schemas import AuthorPaperRecord


class ArxivDailyService:
    def __init__(self, client: ArxivClient, html_parser: ArxivHtmlParser) -> None:
        self.client = client
        self.html_parser = html_parser

    def collect_daily_author_records(
        self, query_date: date, categories: list[str]
    ) -> list[AuthorPaperRecord]:
        papers = self.client.query_papers_by_date(query_date=query_date, categories=categories)
        records: list[AuthorPaperRecord] = []
        for paper in papers:
            paper = self.html_parser.enrich_missing_affiliations(paper)
            for author in paper.authors:
                records.append(
                    AuthorPaperRecord(
                        author_name=author.name,
                        affiliation=author.affiliation,
                        paper_title=paper.title,
                        arxiv_id=paper.arxiv_id,
                        paper_url=paper.paper_url,
                        published_at=paper.published_at,
                    )
                )
        records.sort(key=lambda item: (item.author_name.lower(), item.paper_title.lower()))
        return records
