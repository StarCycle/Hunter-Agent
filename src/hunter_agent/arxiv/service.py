from __future__ import annotations

from datetime import date
from typing import Callable

from hunter_agent.arxiv.client import ArxivClient
from hunter_agent.arxiv.parser import ArxivHtmlParser
from hunter_agent.common.schemas import ArxivPaperAffiliationRecord
from hunter_agent.common.utils import iter_date_range


class ArxivDailyService:
    def __init__(self, client: ArxivClient, html_parser: ArxivHtmlParser) -> None:
        self.client = client
        self.html_parser = html_parser

    def collect_daily_paper_records(
        self,
        query_date: date,
        categories: list[str],
        progress_cb: Callable[[str], None] | None = None,
    ) -> list[ArxivPaperAffiliationRecord]:
        if progress_cb:
            progress_cb(
                f"Requesting arXiv API (date={query_date.isoformat()} categories={categories})"
            )

        papers = self.client.query_papers_by_date(query_date=query_date, categories=categories)
        if progress_cb:
            progress_cb(
                f"arXiv API returned {len(papers)} papers, extracting author list and affiliation_info"
            )

        records: list[ArxivPaperAffiliationRecord] = []
        total = len(papers)
        for index, paper in enumerate(papers, start=1):
            paper = self.html_parser.enrich_affiliation_info(paper)
            records.append(
                ArxivPaperAffiliationRecord(
                    paper_title=paper.title,
                    paper_url=paper.paper_url,
                    authors=[author.name for author in paper.authors],
                    affiliation_info=paper.affiliation_info,
                    paper_summary=paper.summary,
                )
            )
            if progress_cb and (index == total or index % 20 == 0):
                progress_cb(f"Processed {index}/{total} papers")

        records.sort(key=lambda item: item.paper_title.lower())
        if progress_cb:
            progress_cb(f"Paper records built, total {len(records)}")
        return records


class ArxivRangeService:
    def __init__(self, daily_service: ArxivDailyService) -> None:
        self.daily_service = daily_service

    def collect_range_paper_records(
        self,
        start_date: date,
        end_date: date,
        categories: list[str],
        progress_cb: Callable[[str], None] | None = None,
    ) -> list[dict]:
        days: list[dict] = []
        total_days = (end_date - start_date).days + 1
        for offset, query_date in enumerate(iter_date_range(start_date, end_date), start=1):
            if progress_cb:
                progress_cb(
                    f"Collecting {query_date.isoformat()} ({offset}/{total_days})"
                )
            records = self.daily_service.collect_daily_paper_records(
                query_date=query_date,
                categories=categories,
                progress_cb=progress_cb,
            )
            days.append(
                {
                    "date": query_date.isoformat(),
                    "records": [record.model_dump() for record in records],
                }
            )
        return days
