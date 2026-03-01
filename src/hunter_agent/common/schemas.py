from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from hunter_agent.common.enums import PROJECT_CATEGORIES


class ArxivSkillInput(BaseModel):
    date: str = Field(description="Query date in YYYY-MM-DD.")
    categories: list[str] = Field(default_factory=lambda: ["cs.RO"])


class AuthorPaperRecord(BaseModel):
    author_name: str
    affiliation: str | None = None
    paper_title: str
    arxiv_id: str
    paper_url: str
    published_at: str | None = None


class ArxivSkillOutput(BaseModel):
    date: str
    records: list[AuthorPaperRecord]


class TalentProfile(BaseModel):
    name: str
    wechat: str | None = None
    phone: str | None = None
    email: str | None = None
    project_categories: list[str] = Field(default_factory=list)
    education: str | None = None
    institution: str | None = None
    grade_or_years: str | None = None
    resume_pdf: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_project_categories(self) -> "TalentProfile":
        for item in self.project_categories:
            if item in PROJECT_CATEGORIES:
                continue
            if item.startswith("其它:"):
                continue
            raise ValueError(
                f"Unsupported project category: {item}. "
                f"Allowed: {PROJECT_CATEGORIES} or use '其它:自定义内容'."
            )
        return self


class SkillBInput(BaseModel):
    action: Literal["find", "upsert"]
    name: str | None = None
    profile: TalentProfile | None = None

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
    grade_or_years: str | None = None
    resume_pdf: str | None = None
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


class SkillBFindOutput(BaseModel):
    action: Literal["find"] = "find"
    name: str
    matches: list[TalentView]


class SkillBUpsertOutput(BaseModel):
    action: Literal["upsert"] = "upsert"
    profile: TalentView
