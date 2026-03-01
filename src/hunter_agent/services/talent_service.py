from __future__ import annotations

from hunter_agent.common.schemas import TalentProfile
from hunter_agent.db.repo import TalentRepository


class TalentService:
    def __init__(self, repo: TalentRepository) -> None:
        self.repo = repo

    def find_by_name(self, name: str) -> list[dict]:
        return self.repo.find_talents_by_name(name)

    def upsert(self, profile: TalentProfile) -> dict:
        return self.repo.upsert_talent(profile)
