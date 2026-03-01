from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Iterable
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

import requests


ARXIV_API_ENDPOINT = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


@dataclass
class ArxivAuthor:
    name: str
    affiliation: str | None = None


@dataclass
class ArxivPaper:
    arxiv_id: str
    title: str
    paper_url: str
    published_at: str | None
    categories: list[str] = field(default_factory=list)
    authors: list[ArxivAuthor] = field(default_factory=list)


class ArxivClient:
    def __init__(self, timeout_seconds: int = 20, max_results: int = 2000) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_results = max_results
        self.session = requests.Session()

    def query_papers_by_date(
        self,
        query_date: date,
        categories: Iterable[str],
    ) -> list[ArxivPaper]:
        cat_query = " OR ".join(f"cat:{c}" for c in categories)
        date_token = query_date.strftime("%Y%m%d")
        submitted_range = f"submittedDate:[{date_token}0000 TO {date_token}2359]"
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
                aff = author.findtext(
                    "arxiv:affiliation", default=None, namespaces=NS
                )
                aff = aff.strip() if isinstance(aff, str) else None
                if name:
                    authors.append(ArxivAuthor(name=name, affiliation=aff))
            if arxiv_id and title:
                papers.append(
                    ArxivPaper(
                        arxiv_id=arxiv_id,
                        title=title,
                        paper_url=paper_url,
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
