from __future__ import annotations

from typing import Callable
from hunter_agent.arxiv.client import ArxivClient
from hunter_agent.arxiv.parser import ArxivHtmlParser
from hunter_agent.arxiv.service import ArxivDailyService
from hunter_agent.common.schemas import ArxivSkillInput, ArxivSkillOutput
from hunter_agent.common.utils import parse_iso_date
from hunter_agent.db.repo import TalentRepository


def run_arxiv_robotics_daily_collector(
    payload: dict,
    arxiv_client: ArxivClient,
    html_parser: ArxivHtmlParser,
    repo: TalentRepository | None = None,
    persist_mentions: bool = False,
    progress_cb: Callable[[str], None] | None = None,
) -> dict:
    input_obj = ArxivSkillInput.model_validate(payload)
    query_date = parse_iso_date(input_obj.date)
    service = ArxivDailyService(client=arxiv_client, html_parser=html_parser)
    records = service.collect_daily_paper_records(
        query_date=query_date,
        categories=input_obj.categories,
        progress_cb=progress_cb,
    )
    if persist_mentions and repo is not None and records:
        if progress_cb:
            progress_cb("Persisting paper and author mentions to SQLite")
        repo.save_arxiv_mentions(
            source_date=input_obj.date,
            records=records,
            categories=input_obj.categories,
        )
    if progress_cb:
        progress_cb("Finished")
    return ArxivSkillOutput(date=input_obj.date, records=records).model_dump()
