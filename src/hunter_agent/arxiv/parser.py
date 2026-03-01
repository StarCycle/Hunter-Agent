from __future__ import annotations

from bs4 import BeautifulSoup
import requests

from hunter_agent.arxiv.client import ArxivPaper
from hunter_agent.common.utils import normalize_name


class ArxivHtmlParser:
    def __init__(self, timeout_seconds: int = 20) -> None:
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()

    def enrich_missing_affiliations(self, paper: ArxivPaper) -> ArxivPaper:
        if not paper.paper_url:
            return paper
        if not any(not author.affiliation for author in paper.authors):
            return paper
        author_pairs = self.fetch_author_affiliations(paper.paper_url)
        if not author_pairs:
            return paper

        aff_by_name = {normalize_name(name): aff for name, aff in author_pairs if aff}
        for idx, author in enumerate(paper.authors):
            if author.affiliation:
                continue
            exact = aff_by_name.get(normalize_name(author.name))
            if exact:
                author.affiliation = exact
                continue
            if idx < len(author_pairs):
                author.affiliation = author_pairs[idx][1]
        return paper

    def fetch_author_affiliations(self, paper_url: str) -> list[tuple[str, str | None]]:
        response = self.session.get(paper_url, timeout=self.timeout_seconds)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        names = [
            node.get("content", "").strip()
            for node in soup.find_all("meta", attrs={"name": "citation_author"})
            if node.get("content")
        ]
        insts = [
            node.get("content", "").strip()
            for node in soup.find_all(
                "meta", attrs={"name": "citation_author_institution"}
            )
            if node.get("content")
        ]
        if not names:
            return []

        pairs: list[tuple[str, str | None]] = []
        for idx, name in enumerate(names):
            affiliation = insts[idx] if idx < len(insts) else None
            pairs.append((name, affiliation))
        return pairs
