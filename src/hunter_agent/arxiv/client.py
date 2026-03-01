from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
import re
from typing import Iterable
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests


ARXIV_API_ENDPOINT = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


@dataclass
class ArxivAuthor:
    name: str


@dataclass
class ArxivPaper:
    arxiv_id: str
    title: str
    paper_url: str
    html_url: str
    published_at: str | None
    categories: list[str] = field(default_factory=list)
    authors: list[ArxivAuthor] = field(default_factory=list)
    affiliation_info: str | None = None


class ArxivClient:
    def __init__(
        self,
        timeout_seconds: int = 20,
        max_results: int = 2000,
        local_timezone: str = "Asia/Shanghai",
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_results = max_results
        self.local_timezone = local_timezone
        self.session = requests.Session()

    def query_papers_by_date(
        self,
        query_date: date,
        categories: Iterable[str],
    ) -> list[ArxivPaper]:
        cat_query = " OR ".join(f"cat:{c}" for c in categories)
        submitted_range = self.build_submitted_date_range(query_date)
        search_query = f"({cat_query}) AND {submitted_range}"
        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": self.max_results,
            "sortBy": "submittedDate",
            "sortOrder": "ascending",
        }
        response = self.session.get(
            ARXIV_API_ENDPOINT, params=params, timeout=self.timeout_seconds
        )
        response.raise_for_status()
        return self._parse_feed(response.text)

    def build_submitted_date_range(self, query_date: date) -> str:
        tz = _resolve_timezone(self.local_timezone)
        local_start = datetime.combine(query_date, time(0, 0), tzinfo=tz)
        local_end_exclusive = local_start + timedelta(days=1)
        utc_start = local_start.astimezone(timezone.utc)
        utc_end = (local_end_exclusive - timedelta(minutes=1)).astimezone(timezone.utc)
        start_token = utc_start.strftime("%Y%m%d%H%M")
        end_token = utc_end.strftime("%Y%m%d%H%M")
        return f"submittedDate:[{start_token} TO {end_token}]"

    def _parse_feed(self, xml_text: str) -> list[ArxivPaper]:
        root = ET.fromstring(xml_text)
        papers: list[ArxivPaper] = []
        for entry in root.findall("atom:entry", NS):
            paper_url = entry.findtext("atom:id", default="", namespaces=NS).strip()
            arxiv_id = self._extract_arxiv_id_from_url(paper_url)
            title = " ".join(
                entry.findtext("atom:title", default="", namespaces=NS).split()
            )
            published_at = entry.findtext("atom:published", default=None, namespaces=NS)
            categories = [
                node.attrib.get("term", "").strip()
                for node in entry.findall("atom:category", NS)
                if node.attrib.get("term")
            ]
            authors: list[ArxivAuthor] = []
            for author in entry.findall("atom:author", NS):
                name = author.findtext("atom:name", default="", namespaces=NS).strip()
                if name:
                    authors.append(ArxivAuthor(name=name))
            if arxiv_id and title:
                papers.append(
                    ArxivPaper(
                        arxiv_id=arxiv_id,
                        title=title,
                        paper_url=paper_url,
                        html_url=self._build_html_url(arxiv_id),
                        published_at=published_at,
                        categories=categories,
                        authors=authors,
                    )
                )
        return papers

    @staticmethod
    def _extract_arxiv_id_from_url(paper_url: str) -> str:
        parsed = urlparse(paper_url)
        if not parsed.path:
            return ""
        return parsed.path.split("/")[-1]

    @staticmethod
    def _build_html_url(arxiv_id: str) -> str:
        if not arxiv_id:
            return ""
        return f"https://arxiv.org/html/{arxiv_id}"


def _resolve_timezone(tz_name: str):
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        # Windows/Python environments may not ship IANA tz database.
        if tz_name in {"Asia/Shanghai", "Asia/Hong_Kong", "Asia/Singapore"}:
            return timezone(timedelta(hours=8))
        if tz_name in {"UTC", "Etc/UTC"}:
            return timezone.utc
        match = re.fullmatch(r"([+-])(\d{2}):?(\d{2})", tz_name or "")
        if match:
            sign = 1 if match.group(1) == "+" else -1
            hours = int(match.group(2))
            minutes = int(match.group(3))
            return timezone(sign * timedelta(hours=hours, minutes=minutes))
        return timezone.utc
