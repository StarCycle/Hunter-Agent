from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from hunter_agent.common.utils import normalize_name, normalize_project_category, parse_iso_date


class ArxivSkillInput(BaseModel):
    date: str = Field(description="Query date in YYYY-MM-DD.")
    categories: list[str] = Field(default_factory=lambda: ["cs.RO"])


class ArxivRangeInput(BaseModel):
    start_date: str = Field(description="Range start date in YYYY-MM-DD.")
    end_date: str = Field(description="Range end date in YYYY-MM-DD.")
    categories: list[str] = Field(default_factory=lambda: ["cs.RO"])

    @model_validator(mode="after")
    def validate_date_order(self) -> "ArxivRangeInput":
        if parse_iso_date(self.start_date) > parse_iso_date(self.end_date):
            raise ValueError("start_date must be earlier than or equal to end_date.")
        return self


class ArxivPaperAffiliationRecord(BaseModel):
    paper_title: str
    paper_url: str
    authors: list[str] = Field(default_factory=list)
    affiliation_info: str | None = None
    paper_summary: str | None = None


class ArxivSkillOutput(BaseModel):
    date: str
    records: list[ArxivPaperAffiliationRecord]


class ArxivRangeDayOutput(BaseModel):
    date: str
    records: list[ArxivPaperAffiliationRecord]


class ArxivRangeOutput(BaseModel):
    start_date: str
    end_date: str
    days: list[ArxivRangeDayOutput]


class AuthorCandidatePaperEvidence(BaseModel):
    source_date: str
    paper_title: str
    paper_url: str
    affiliation_info: str | None = None
    paper_summary: str | None = None


class AuthorCandidate(BaseModel):
    author_name: str
    normalized_name: str
    paper_count: int
    source_dates: list[str] = Field(default_factory=list)
    affiliation_clues: list[str] = Field(default_factory=list)
    papers: list[AuthorCandidatePaperEvidence] = Field(default_factory=list)


class AuthorCandidateOutput(BaseModel):
    start_date: str | None = None
    end_date: str | None = None
    authors: list[AuthorCandidate]


class TalentProfile(BaseModel):
    name: str
    wechat: str | None = None
    phone: str | None = None
    email: str | None = None
    project_categories: list[str] = Field(default_factory=list)
    education: str | None = None
    institution: str | None = None
    position: str | None = None
    grade_or_years: str | None = None
    city: str | None = None
    country: str | None = None
    graduation_time: str | None = None
    research_fields: str | None = None
    homepage_url: str | None = None
    resume_pdf: str | None = None
    source_links: str | None = None
    evidence_summary: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_project_categories(self) -> "TalentProfile":
        self.project_categories = [
            normalize_project_category(item) for item in self.project_categories
        ]
        return self

    @model_validator(mode="after")
    def validate_position(self) -> "TalentProfile":
        allowed_positions = {
            "undergraduate",
            "masters",
            "phd",
            "postdoc",
            "faculty",
            "academia",
            "industry",
        }
        if self.position and self.position not in allowed_positions:
            raise ValueError(
                "position must be one of: undergraduate, masters, phd, postdoc, faculty, academia, industry."
            )
        return self


class SkillBInput(BaseModel):
    action: Literal["find", "upsert", "export"]
    name: str | None = None
    profile: TalentProfile | None = None
    out_csv: str | None = None

    @model_validator(mode="after")
    def validate_action_input(self) -> "SkillBInput":
        if self.action == "find" and not self.name:
            raise ValueError("Field 'name' is required for action=find.")
        if self.action == "upsert" and self.profile is None:
            raise ValueError("Field 'profile' is required for action=upsert.")
        return self


class DedupResult(BaseModel):
    candidate_id: int | None = None
    score: int
    conflict: bool
    reasons: list[str] = Field(default_factory=list)
    forced_insert: bool | None = None


class TalentCore(BaseModel):
    id: int
    name: str
    normalized_name: str
    education: str | None = None
    institution: str | None = None
    position: str | None = None
    grade_or_years: str | None = None
    city: str | None = None
    country: str | None = None
    graduation_time: str | None = None
    research_fields: str | None = None
    homepage_url: str | None = None
    resume_pdf: str | None = None
    source_links: str | None = None
    evidence_summary: str | None = None
    notes: str | None = None
    created_at: str
    updated_at: str


class ContactItem(BaseModel):
    type: Literal["wechat", "phone", "email"]
    value: str
    verified: int
    created_at: str
    updated_at: str


class ProjectTagItem(BaseModel):
    category: str
    other_text: str | None = None
    created_at: str


class TalentView(BaseModel):
    talent: TalentCore
    contacts: list[ContactItem]
    project_tags: list[ProjectTagItem]
    dedup: DedupResult | None = None
    operation: Literal["insert", "update"] | None = None


class TalentBulkUpsertOutput(BaseModel):
    action: Literal["bulk-upsert"] = "bulk-upsert"
    profiles: list[TalentView]


class SkillBFindOutput(BaseModel):
    action: Literal["find"] = "find"
    name: str
    matches: list[TalentView]


class SkillBUpsertOutput(BaseModel):
    action: Literal["upsert"] = "upsert"
    profile: TalentView


class SkillBExportOutput(BaseModel):
    action: Literal["export"] = "export"
    output: str


class TalentBulkUpsertInput(BaseModel):
    profiles: list[TalentProfile]

    @model_validator(mode="after")
    def validate_profiles(self) -> "TalentBulkUpsertInput":
        if not self.profiles:
            raise ValueError("At least one profile is required for bulk upsert.")
        return self


class AuthorCandidateSeed(BaseModel):
    source_date: str
    paper_title: str
    paper_url: str
    authors: list[str] = Field(default_factory=list)
    affiliation_info: str | None = None
    paper_summary: str | None = None

    @property
    def normalized_authors(self) -> list[tuple[str, str]]:
        return [(author_name, normalize_name(author_name)) for author_name in self.authors]
