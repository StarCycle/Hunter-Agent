from __future__ import annotations

import unittest

from hunter_agent.arxiv.parser import ArxivHtmlParser


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        return None


class _FakeSession:
    def __init__(self, html_text: str) -> None:
        self.html_text = html_text

    def get(self, url, timeout):  # noqa: ANN001
        return _FakeResponse(self.html_text)


class TestArxivHtmlParser(unittest.TestCase):
    def test_extract_affiliation_info_snippet(self) -> None:
        html_text = """
        <html><body>
        License: arXiv.org perpetual non-exclusive license
        arXiv:2602.01153v1 [cs.RO] 01 Feb 2026
        UniForce: A Unified Latent Force Model
        Zhuo Chen1, Fei Ni2, Kaiyao Luo1
        1 University A, 2 University B
        Abstract
        This is abstract.
        </body></html>
        """
        parser = ArxivHtmlParser()
        parser.session = _FakeSession(html_text)  # type: ignore[assignment]
        snippet = parser.fetch_affiliation_info("https://arxiv.org/html/2602.01153v1")
        assert snippet is not None
        self.assertIn("UniForce", snippet)
        self.assertIn("University A", snippet)
        self.assertNotIn("This is abstract.", snippet)


if __name__ == "__main__":
    unittest.main()
