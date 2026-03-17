from __future__ import annotations

from datetime import date
from typing import Callable

from hunter_agent.arxiv.client import ArxivClient
from hunter_agent.arxiv.parser import ArxivHtmlParser
from hunter_agent.arxiv.service import ArxivDailyService, ArxivRangeService
from hunter_agent.common.schemas import AuthorCandidateSeed
from hunter_agent.common.utils import parse_iso_date, previous_calendar_week_range
from hunter_agent.services.author_candidate_service import AuthorCandidateService


def run_arxiv_range_authors(
    payload: dict,
    arxiv_client: ArxivClient,
    html_parser: ArxivHtmlParser,
    progress_cb: Callable[[str], None] | None = None,
    today: date | None = None,
) -> dict:
    start_date, end_date = _resolve_date_range(
        start_date_text=payload.get("start_date"),
        end_date_text=payload.get("end_date"),
        today=today,
    )
    categories = payload.get("categories") or ["cs.RO"]
    daily_service = ArxivDailyService(client=arxiv_client, html_parser=html_parser)
    range_service = ArxivRangeService(daily_service=daily_service)
    days = range_service.collect_range_paper_records(
        start_date=start_date,
        end_date=end_date,
        categories=categories,
        progress_cb=progress_cb,
    )
    seeds: list[AuthorCandidateSeed] = []
    for day in days:
        for record in day["records"]:
            seeds.append(
                AuthorCandidateSeed(
                    source_date=day["date"],
                    paper_title=record["paper_title"],
                    paper_url=record["paper_url"],
                    authors=record["authors"],
                    affiliation_info=record.get("affiliation_info"),
                    paper_summary=record.get("paper_summary"),
                )
            )
    return AuthorCandidateService().build_candidates(
        seeds=seeds,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
    )


def _resolve_date_range(
    start_date_text: str | None,
    end_date_text: str | None,
    today: date | None = None,
) -> tuple[date, date]:
    if bool(start_date_text) != bool(end_date_text):
        raise ValueError("start_date and end_date must be provided together.")
    if start_date_text and end_date_text:
        start_date = parse_iso_date(start_date_text)
        end_date = parse_iso_date(end_date_text)
        if start_date > end_date:
            raise ValueError("start_date must be earlier than or equal to end_date.")
        return start_date, end_date
    return previous_calendar_week_range(anchor_date=today)
