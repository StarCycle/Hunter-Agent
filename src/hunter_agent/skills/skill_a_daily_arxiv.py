from __future__ import annotations

from hunter_agent.arxiv.client import ArxivClient
from hunter_agent.arxiv.parser import ArxivHtmlParser
from hunter_agent.arxiv.service import ArxivDailyService
from hunter_agent.common.schemas import ArxivSkillInput, ArxivSkillOutput
from hunter_agent.common.utils import parse_iso_date
from hunter_agent.db.repo import TalentRepository


def run_skill_a(
    payload: dict,
    arxiv_client: ArxivClient,
    html_parser: ArxivHtmlParser,
    repo: TalentRepository | None = None,
    persist_mentions: bool = False,
) -> dict:
    input_obj = ArxivSkillInput.model_validate(payload)
    query_date = parse_iso_date(input_obj.date)
    service = ArxivDailyService(client=arxiv_client, html_parser=html_parser)
    records = service.collect_daily_author_records(
        query_date=query_date,
        categories=input_obj.categories,
    )
    if persist_mentions and repo is not None and records:
        repo.save_arxiv_mentions(
            source_date=input_obj.date,
            records=records,
            categories=input_obj.categories,
        )
    return ArxivSkillOutput(date=input_obj.date, records=records).model_dump()
