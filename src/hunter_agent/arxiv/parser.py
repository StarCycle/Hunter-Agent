from __future__ import annotations

from bs4 import BeautifulSoup
import requests

from hunter_agent.arxiv.client import ArxivPaper


class ArxivHtmlParser:
    def __init__(self, timeout_seconds: int = 20) -> None:
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()

    def enrich_affiliation_info(self, paper: ArxivPaper) -> ArxivPaper:
        html_url = paper.html_url or ""
        if not html_url:
            return paper
        paper.affiliation_info = self.fetch_affiliation_info(html_url)
        return paper

    def fetch_affiliation_info(self, html_url: str) -> str | None:
        try:
            response = self.session.get(html_url, timeout=self.timeout_seconds)
            response.raise_for_status()
        except requests.RequestException:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        snippet = self._extract_by_ltx_header_blocks(soup)
        if snippet:
            return snippet
        return self._extract_by_body_fallback(soup)

    def _extract_by_ltx_header_blocks(self, soup: BeautifulSoup) -> str | None:
        title_node = soup.select_one(".ltx_title_document")
        title_text = _clean_whitespace(title_node.get_text(" ", strip=True)) if title_node else ""

        creator_node = soup.select_one(".ltx_authors") or soup.select_one(".ltx_creator")
        creator_text = (
            _clean_whitespace(creator_node.get_text(" ", strip=True)) if creator_node else ""
        )

        lines: list[str] = []
        if title_text:
            lines.append(f"Title: {title_text}")
        if creator_text:
            lines.append(f"AuthorsAndAffiliations: {creator_text}")

        if not lines:
            return None
        snippet = "\n".join(lines).strip()
        if len(snippet) > 1800:
            snippet = snippet[:1800].rstrip()
        return snippet or None

    def _extract_by_body_fallback(self, soup: BeautifulSoup) -> str | None:
        body = soup.body
        if body is None:
            return None
        raw_text = body.get_text("\n", strip=True)
        if not raw_text:
            return None
        lines = [_clean_whitespace(line) for line in raw_text.splitlines() if line.strip()]
        if not lines:
            return None

        blocked = {
            "Report GitHub Issue",
            "Submit without GitHub",
            "Submit in GitHub",
            "Back to arXiv",
            "Why HTML?",
            "Report Issue",
            "Back to Abstract",
            "Download PDF",
        }
        snippet_lines: list[str] = []
        for line in lines[:120]:
            if line in blocked:
                continue
            if line.lower().startswith("abstract"):
                break
            snippet_lines.append(line)
            if len(snippet_lines) >= 25:
                break
        if not snippet_lines:
            return None

        snippet = "\n".join(snippet_lines).strip()
        if len(snippet) > 1800:
            snippet = snippet[:1800].rstrip()
        return snippet or None


def _clean_whitespace(text: str) -> str:
    return " ".join((text or "").split())
