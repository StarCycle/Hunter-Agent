from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TalentRecord:
    id: int
    name: str
    normalized_name: str
    education: str | None
    institution: str | None
    grade_or_years: str | None
    city: str | None
    country: str | None
    graduation_time: str | None
    research_fields: str | None
    homepage_url: str | None
    resume_pdf: str | None
    source_links: str | None
    evidence_summary: str | None
    notes: str | None
    created_at: str
    updated_at: str
