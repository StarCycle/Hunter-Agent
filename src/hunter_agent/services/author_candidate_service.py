from __future__ import annotations

from hunter_agent.common.schemas import (
    AuthorCandidate,
    AuthorCandidateOutput,
    AuthorCandidatePaperEvidence,
    AuthorCandidateSeed,
)


class AuthorCandidateService:
    def build_candidates(
        self,
        seeds: list[AuthorCandidateSeed],
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        grouped: dict[str, dict] = {}

        for seed in seeds:
            for author_name, normalized_name in seed.normalized_authors:
                item = grouped.setdefault(
                    normalized_name,
                    {
                        "author_name": author_name,
                        "normalized_name": normalized_name,
                        "source_dates": set(),
                        "affiliation_clues": set(),
                        "papers": [],
                    },
                )
                item["source_dates"].add(seed.source_date)
                if seed.affiliation_info:
                    item["affiliation_clues"].add(seed.affiliation_info)
                item["papers"].append(
                    AuthorCandidatePaperEvidence(
                        source_date=seed.source_date,
                        paper_title=seed.paper_title,
                        paper_url=seed.paper_url,
                        affiliation_info=seed.affiliation_info,
                        paper_summary=seed.paper_summary,
                    )
                )

        authors: list[AuthorCandidate] = []
        for item in grouped.values():
            papers = sorted(
                item["papers"],
                key=lambda paper: (paper.source_date, paper.paper_title.lower()),
            )
            authors.append(
                AuthorCandidate(
                    author_name=item["author_name"],
                    normalized_name=item["normalized_name"],
                    paper_count=len(papers),
                    source_dates=sorted(item["source_dates"]),
                    affiliation_clues=sorted(item["affiliation_clues"]),
                    papers=papers,
                )
            )

        authors.sort(key=lambda author: (-author.paper_count, author.author_name.lower()))
        return AuthorCandidateOutput(
            start_date=start_date,
            end_date=end_date,
            authors=authors,
        ).model_dump()
